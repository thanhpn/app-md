"""Pushes a Source's crawled products into dvc-api/apps/reviews as
real Category/Product/Retailer/Offer rows, via ReviewsClient. Manually
triggered per-source (admin UI "Đẩy sang Review" button) — not run
automatically after every crawl, so a human picks the target category and
can review crawl results first.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CrawledProduct, Source
from app.services.reviews_client import ReviewsClient, ReviewsClientError
from app.services.slugify import slugify


@dataclass
class PushResult:
    pushed_new: int = 0
    pushed_updated: int = 0
    errors: list[str] = field(default_factory=list)


def _product_payload(category_id: str, crawled: CrawledProduct) -> dict:
    return {
        "category_id": category_id,
        "name": crawled.name,
        "slug": slugify(crawled.name),
        "brand": crawled.brand,
        "images": crawled.images or [],
        "specs": crawled.specs or {},
    }


def _offer_payload(product_id: str, retailer_id: str, crawled: CrawledProduct) -> dict:
    return {
        "product_id": product_id,
        "retailer_id": retailer_id,
        "price": float(crawled.price),
        "currency": crawled.currency,
        "affiliate_url": crawled.affiliate_url or crawled.url,
        "in_stock": True,
        "source": "crawler",
    }


async def push_source(session: AsyncSession, source: Source, category_name: str) -> PushResult:
    result = PushResult()
    reviews_client = ReviewsClient()

    rows = await session.execute(select(CrawledProduct).where(CrawledProduct.source_id == source.id))
    products = list(rows.scalars())

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        if source.reviews_category_id is None:
            try:
                source.reviews_category_id = await reviews_client.get_or_create_category(client, category_name, slugify(category_name))
            except ReviewsClientError as exc:
                result.errors.append(f"tạo/tìm danh mục thất bại: {exc}")
                return result

        if source.reviews_retailer_id is None:
            try:
                source.reviews_retailer_id = await reviews_client.get_or_create_retailer(
                    client, source.name, slugify(source.name), source.base_url
                )
            except ReviewsClientError as exc:
                result.errors.append(f"tạo/tìm nhà bán thất bại: {exc}")
                return result

        category_id = source.reviews_category_id
        retailer_id = source.reviews_retailer_id

        for product in products:
            if product.price is None:
                result.errors.append(f"bỏ qua '{product.name}' — không có giá")
                continue
            # dvc-api gateway rate-limits per IP at 240 rpm (4 req/s) sustained,
            # burst 60 — each product costs up to 4 requests, so this keeps the
            # sustained rate at ~3.3 req/s once the initial burst is used up.
            # ReviewsClient also retries individual 429s as a second line of defense.
            await asyncio.sleep(0.8)
            try:
                if product.pushed_product_id is None:
                    product_id = await reviews_client.create_product(client, _product_payload(category_id, product))
                    # Link immediately after create succeeds — if set_product_status
                    # below then fails (e.g. rate limit), the retry must go through
                    # update_product, not create another product with the same slug.
                    product.pushed_product_id = product_id
                    await reviews_client.set_product_status(client, product_id, "published")
                    result.pushed_new += 1
                else:
                    product_id = product.pushed_product_id
                    await reviews_client.update_product(client, product_id, _product_payload(category_id, product))
                    result.pushed_updated += 1

                offers = await reviews_client.list_offers(client, product_id)
                existing_offer = next((o for o in offers if o["retailer_id"] == retailer_id), None)
                offer_payload = _offer_payload(product_id, retailer_id, product)
                if existing_offer is None:
                    await reviews_client.create_offer(client, offer_payload)
                else:
                    await reviews_client.update_offer(client, existing_offer["id"], offer_payload)

                product.pushed_at = datetime.now(UTC)
            except ReviewsClientError as exc:
                result.errors.append(f"đẩy '{product.name}' thất bại: {exc}")

    await session.commit()
    return result
