"""adapter_key = 'generic_article' — for review/blog/comparison sites where
writing per-site selectors isn't worth it: uses trafilatura's generic
content-extraction heuristics (same approach as read-it-later apps) to pull
title/author/date/body out of arbitrary article HTML. Works out of the box
on most blog/news layouts without any selector config — the main lever for
a new site is just which URLs to crawl.

Expected Source.config shape:
{
  "article_urls": ["https://blog.com/post-1", ...],   # OR:
  "seed_urls": ["https://blog.com/category/phones"],  # listing pages to discover article links from
  "article_link_selector": "a.post-title",            # required if using seed_urls
  "article_link_url_pattern": "/tin-tuc/",             # optional regex (re.search) — drops discovered links that
                                                        # don't match, e.g. to exclude nav/category links caught by
                                                        # a broad selector
  "max_items": 50
}
"""

import httpx
import trafilatura
from bs4 import BeautifulSoup

from app.adapters.base import Adapter, AdapterResult, FetchedPage, ParsedContent, register
from app.adapters.utils import filter_urls_by_pattern, resolve_url

_TIMEOUT = httpx.Timeout(20.0)
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; dvc-worker/1.0; +https://github.com/1MobileApp)"}


@register("generic_article")
class GenericArticleAdapter(Adapter):
    async def run(self) -> AdapterResult:
        pages: list[FetchedPage] = []
        contents: list[ParsedContent] = []
        errors: list[str] = []

        async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True) as client:
            urls = await self._resolve_article_urls(client, errors)
            max_items = int(self.config.get("max_items", 50))
            for url in urls[:max_items]:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    errors.append(f"fetch failed {url}: {exc}")
                    continue

                pages.append(FetchedPage(url=url, content=resp.text))
                extracted = trafilatura.extract(
                    resp.text, url=url, output_format="json", with_metadata=True, favor_precision=True
                )
                if not extracted:
                    errors.append(f"extraction produced nothing for {url}")
                    continue

                import json

                data = json.loads(extracted)
                body = data.get("text") or ""
                if not body:
                    errors.append(f"extracted empty body for {url}")
                    continue

                contents.append(
                    ParsedContent(
                        external_ref=url,
                        content_type="review_article",
                        body=body,
                        title=data.get("title"),
                        author=data.get("author"),
                        published_at=data.get("date"),
                    )
                )

        return AdapterResult(pages=pages, contents=contents, errors=errors)

    async def _resolve_article_urls(self, client: httpx.AsyncClient, errors: list[str]) -> list[str]:
        explicit = self.config.get("article_urls")
        if explicit:
            return list(dict.fromkeys(explicit))

        seed_urls = self.config.get("seed_urls", [])
        link_selector = self.config.get("article_link_selector")
        if not seed_urls or not link_selector:
            errors.append("config has neither article_urls nor (seed_urls + article_link_selector)")
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
        return filter_urls_by_pattern(deduped, self.config.get("article_link_url_pattern"))
