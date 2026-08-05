"""adapter_key = 'shopee_affiliate' — Shopee Affiliate Open API (GraphQL),
not scraping. Requires an approved Shopee Affiliate account; credentials go
in `.env` (SHOPEE_AFFILIATE_APP_ID/SECRET), never in Source.config.

⚠️ Built from Shopee's publicly documented Affiliate Open API shape
(auth scheme + `productOfferV2` field names), NOT verified against a real
account — nobody on this project has API access yet. Before relying on
this in production: run 1 real query against your own Shopee Affiliate
dashboard's "Open API Explorer" and confirm field names/enum values below
still match (they've been stable across regions/SDKs at time of writing,
but Shopee doesn't publish a versioned public spec).

Expected Source.config shape (all optional except at least one search
scope):
{
  "keyword": "điều hòa",      # search keyword, OR:
  "shop_id": 123456,          # specific shop's offers, OR:
  "product_cat_id": 123,      # Shopee category id
  "sort_type": 2,             # per Shopee's docs/SDKs; meaning not publicly specified, 2 = observed default
  "list_type": 0,             # ditto, 0 = observed default
  "page_size": 20,
  "max_items": 100
}

Auth: `Authorization: SHA256 Credential={app_id}, Timestamp={ts}, Signature={sig}`
where `sig = sha256(app_id + ts + payload + secret).hexdigest()` and
`payload` is the *exact* JSON body bytes sent (signed and sent must match
byte-for-byte, so this module builds the body once and reuses that string).
"""

import hashlib
import time

import httpx

from app.adapters.base import Adapter, AdapterResult, FetchedPage, ParsedProduct, register
from app.config import settings

_QUERY = """
query Fetch($keyword: String, $shopId: Int64, $productCatId: Int64, $sortType: Int, $listType: Int, $page: Int, $limit: Int) {
  productOfferV2(keyword: $keyword, shopId: $shopId, productCatId: $productCatId, sortType: $sortType, listType: $listType, page: $page, limit: $limit) {
    nodes {
      itemId
      productName
      productLink
      offerLink
      imageUrl
      priceMin
      priceMax
      shopName
      ratingStar
      commissionRate
    }
  }
}
"""


def sign_request(app_id: str, secret: str, timestamp: int, payload: str) -> str:
    """Pure — split out from _post so it's unit-testable without network."""
    raw = f"{app_id}{timestamp}{payload}{secret}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_products(nodes: list[dict]) -> list[ParsedProduct]:
    """Pure — turns 1 page of productOfferV2 nodes into ParsedProduct.
    priceMin is used as the display price (Shopee returns a min/max range
    across variants; there's no single "the" price for a multi-variant
    listing) — this is a simplification, not the price of a specific SKU."""
    products = []
    for node in nodes:
        name = node.get("productName")
        product_link = node.get("productLink")
        if not name or not product_link:
            continue
        price_raw = node.get("priceMin")
        try:
            price = float(price_raw) if price_raw not in (None, "") else None
        except (TypeError, ValueError):
            price = None
        images = [node["imageUrl"]] if node.get("imageUrl") else []
        specs = {}
        if node.get("shopName"):
            specs["Cửa hàng"] = node["shopName"]
        if node.get("ratingStar"):
            specs["Đánh giá"] = str(node["ratingStar"])

        products.append(
            ParsedProduct(
                url=product_link,
                name=name,
                external_id=str(node["itemId"]) if node.get("itemId") is not None else None,
                price=price,
                images=images,
                specs=specs,
                affiliate_url=node.get("offerLink") or None,
            )
        )
    return products


@register("shopee_affiliate")
class ShopeeAffiliateAdapter(Adapter):
    async def run(self) -> AdapterResult:
        if not settings.shopee_affiliate_app_id or not settings.shopee_affiliate_secret:
            return AdapterResult(pages=[], errors=["SHOPEE_AFFILIATE_APP_ID/SECRET chưa cấu hình trong .env"])

        max_items = int(self.config.get("max_items", 100))
        page_size = int(self.config.get("page_size", 20))

        variables_base = {
            "keyword": self.config.get("keyword"),
            "shopId": self.config.get("shop_id"),
            "productCatId": self.config.get("product_cat_id"),
            "sortType": self.config.get("sort_type", 2),
            "listType": self.config.get("list_type", 0),
            "limit": page_size,
        }
        if not any([variables_base["keyword"], variables_base["shopId"], variables_base["productCatId"]]):
            return AdapterResult(pages=[], errors=["config cần ít nhất 1 trong: keyword, shop_id, product_cat_id"])

        pages: list[FetchedPage] = []
        products: list[ParsedProduct] = []
        errors: list[str] = []

        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            page_num = 1
            while len(products) < max_items:
                variables = {**variables_base, "page": page_num}
                try:
                    nodes, raw_body = await self._fetch_page(client, variables)
                except Exception as exc:  # noqa: BLE001 — 1 failed page must not lose earlier pages' results
                    errors.append(f"page {page_num} failed: {exc}")
                    break

                pages.append(FetchedPage(url=f"shopee_affiliate:page={page_num}", content=raw_body))
                if not nodes:
                    break

                parsed = parse_products(nodes)
                if not parsed:
                    errors.append(f"page {page_num}: {len(nodes)} node(s) nhưng không parse được cái nào")
                products.extend(parsed)
                if len(nodes) < page_size:
                    break  # short page = last page (no pageInfo.hasNextPage relied on — see module docstring)
                page_num += 1

        return AdapterResult(pages=pages, products=products[:max_items], errors=errors)

    async def _fetch_page(self, client: httpx.AsyncClient, variables: dict) -> tuple[list[dict], str]:
        import json

        body = json.dumps({"query": _QUERY, "variables": variables}, separators=(",", ":"))
        timestamp = int(time.time())
        signature = sign_request(settings.shopee_affiliate_app_id, settings.shopee_affiliate_secret, timestamp, body)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={settings.shopee_affiliate_app_id}, Timestamp={timestamp}, Signature={signature}",
        }

        resp = await client.post(settings.shopee_affiliate_api_base_url, content=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        return data["data"]["productOfferV2"]["nodes"], resp.text
