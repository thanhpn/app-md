"""adapter_key = 'generic_html_product' — CSS-selector-driven scraper for a
single product-detail page layout, config-driven so adding a new e-commerce
site is a Source row, not new code.

Expected Source.config shape:
{
  "product_urls": ["https://site.com/p/123", ...],   # OR:
  "seed_urls": ["https://site.com/category/phones"], # listing pages to discover product links from
  "product_link_selector": "a.product-card",         # required if using seed_urls
  "product_link_url_pattern": "/p/\\d+",              # optional regex (re.search) — drops discovered links that don't
                                                       # match, e.g. to exclude sponsored/ad links sharing the same
                                                       # selector as real product links but pointing at a different URL shape
  "max_items": 50,
  "selectors": {
    "name": "h1.product-title",
    "price": ".price",                                # free-form text, parsed by parse_price()
    "brand": ".brand",                                 # optional
    "external_id": ".sku::attr(data-sku)",             # optional
    "images": "img.gallery-img::attr(src)",            # optional, matches ALL elements
    "category_path": ".breadcrumb"                      # optional
  },
  "specs_selector": ".specs-table tr"                  # optional: <th>/<td> or 2x <td> rows -> dict
}

Only static HTML is fetched (httpx, no JS execution) — sites that render
product data client-side via JS are a known limitation, see README.
"""

import httpx
from bs4 import BeautifulSoup

from app.adapters.base import Adapter, AdapterResult, FetchedPage, ParsedProduct, register
from app.adapters.utils import filter_urls_by_pattern, parse_price, parse_selector, resolve_url

_TIMEOUT = httpx.Timeout(20.0)
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; dvc-worker/1.0; +https://github.com/1MobileApp)"}


def _select_text(soup: BeautifulSoup, selector: str) -> str | None:
    css, attr = parse_selector(selector)
    el = soup.select_one(css)
    if el is None:
        return None
    return el.get(attr) if attr else el.get_text(strip=True)


def _select_all(soup: BeautifulSoup, selector: str) -> list[str]:
    css, attr = parse_selector(selector)
    out = []
    for el in soup.select(css):
        val = el.get(attr) if attr else el.get_text(strip=True)
        if val:
            out.append(val)
    return out


def _parse_specs(soup: BeautifulSoup, selector: str) -> dict[str, str]:
    specs: dict[str, str] = {}
    for row in soup.select(selector):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if key:
                specs[key] = value
    return specs


@register("generic_html_product")
class GenericHtmlProductAdapter(Adapter):
    async def run(self) -> AdapterResult:
        pages: list[FetchedPage] = []
        products: list[ParsedProduct] = []
        errors: list[str] = []

        async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True) as client:
            product_urls = await self._resolve_product_urls(client, errors)
            max_items = int(self.config.get("max_items", 50))
            for url in product_urls[:max_items]:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    errors.append(f"fetch failed {url}: {exc}")
                    continue

                pages.append(FetchedPage(url=url, content=resp.text))
                try:
                    product = self._parse_product(url, resp.text)
                    if product is not None:
                        products.append(product)
                    else:
                        errors.append(f"parse produced no name for {url}")
                except Exception as exc:  # noqa: BLE001 — 1 bad page must not abort the whole run
                    errors.append(f"parse failed {url}: {exc}")

        return AdapterResult(pages=pages, products=products, errors=errors)

    async def _resolve_product_urls(self, client: httpx.AsyncClient, errors: list[str]) -> list[str]:
        explicit = self.config.get("product_urls")
        if explicit:
            return list(dict.fromkeys(explicit))

        seed_urls = self.config.get("seed_urls", [])
        link_selector = self.config.get("product_link_selector")
        if not seed_urls or not link_selector:
            errors.append("config has neither product_urls nor (seed_urls + product_link_selector)")
            return []

        found: list[str] = []
        for seed_url in seed_urls:
            try:
                resp = await client.get(seed_url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                errors.append(f"seed fetch failed {seed_url}: {exc}")
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            for el in soup.select(link_selector):
                href = el.get("href")
                if href:
                    found.append(resolve_url(seed_url, href))
        deduped = list(dict.fromkeys(found))
        return filter_urls_by_pattern(deduped, self.config.get("product_link_url_pattern"))

    def _parse_product(self, url: str, html: str) -> ParsedProduct | None:
        soup = BeautifulSoup(html, "lxml")
        selectors = self.config.get("selectors", {})

        name = _select_text(soup, selectors["name"]) if "name" in selectors else None
        if not name:
            return None

        price = parse_price(_select_text(soup, selectors["price"])) if "price" in selectors else None
        brand = _select_text(soup, selectors["brand"]) if "brand" in selectors else None
        external_id = _select_text(soup, selectors["external_id"]) if "external_id" in selectors else None
        category_path = _select_text(soup, selectors["category_path"]) if "category_path" in selectors else None
        images = _select_all(soup, selectors["images"]) if "images" in selectors else []
        images = [resolve_url(url, src) for src in images]
        specs = _parse_specs(soup, self.config["specs_selector"]) if self.config.get("specs_selector") else {}

        return ParsedProduct(
            url=url,
            name=name,
            external_id=external_id,
            brand=brand,
            price=price,
            images=images,
            specs=specs,
            category_path=category_path,
        )
