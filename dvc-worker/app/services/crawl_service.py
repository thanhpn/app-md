from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import AdapterResult, ParsedContent, ParsedProduct, get_adapter
from app.adapters.utils import content_hash
from app.models import CrawledContent, CrawledPriceHistory, CrawledProduct, CrawlRun, RawItem, Source
from app.services.dedupe import classify_raw_item, run_status


async def run_source(session: AsyncSession, source: Source) -> CrawlRun:
    run = CrawlRun(source_id=source.id, status="running")
    session.add(run)
    await session.flush()

    adapter = get_adapter(source.adapter_key, source.config)
    try:
        result: AdapterResult = await adapter.run()
    except Exception as exc:  # noqa: BLE001 — a crashing adapter must still leave a readable run record
        run.status = "failed"
        run.finished_at = datetime.now(UTC)
        run.error_summary = f"adapter crashed: {exc}"[:2000]
        run.errors_count = 1
        await session.commit()
        return run

    raw_item_ids = await _upsert_raw_items(session, source.id, run.id, result)
    items_new = 0
    items_updated = 0

    for product in result.products:
        created = await _upsert_product(session, source.id, raw_item_ids.get(product.url), product)
        items_new += 1 if created else 0
        items_updated += 0 if created else 1

    for content in result.contents:
        created = await _upsert_content(session, source.id, raw_item_ids.get(_content_page_url(content)), content)
        items_new += 1 if created else 0
        items_updated += 0 if created else 1

    items_found = len(result.products) + len(result.contents)
    run.items_found = items_found
    run.items_new = items_new
    run.items_updated = items_updated
    run.errors_count = len(result.errors)
    run.error_summary = "; ".join(result.errors)[:2000] if result.errors else None
    run.status = run_status(run.errors_count, items_new + items_updated)
    run.finished_at = datetime.now(UTC)

    source.last_run_at = run.finished_at

    await session.commit()
    return run


def _content_page_url(content: ParsedContent) -> str:
    # YouTube contents key raw items by watch-url, not the bare video id
    # stored in external_ref — see youtube_channel.py.
    if content.content_type == "youtube_video":
        return f"https://www.youtube.com/watch?v={content.external_ref}"
    return content.external_ref


async def _upsert_raw_items(session: AsyncSession, source_id, run_id, result: AdapterResult) -> dict[str, object]:
    urls = [p.url for p in result.pages]
    existing = {}
    if urls:
        rows = await session.execute(select(RawItem).where(RawItem.source_id == source_id, RawItem.url.in_(urls)))
        existing = {row.url: row for row in rows.scalars()}

    raw_item_ids: dict[str, object] = {}
    for page in result.pages:
        new_hash = content_hash(page.content)
        prior = existing.get(page.url)
        status = classify_raw_item(prior.content_hash if prior else None, new_hash)
        if prior:
            prior.run_id = run_id
            prior.content_hash = new_hash
            prior.raw_content = page.content
            prior.status = status
            raw_item_ids[page.url] = prior.id
        else:
            item = RawItem(source_id=source_id, run_id=run_id, url=page.url, content_hash=new_hash, raw_content=page.content, status=status)
            session.add(item)
            await session.flush()
            raw_item_ids[page.url] = item.id
    return raw_item_ids


async def _upsert_product(session: AsyncSession, source_id, raw_item_id, parsed: ParsedProduct) -> bool:
    existing = (
        await session.execute(select(CrawledProduct).where(CrawledProduct.source_id == source_id, CrawledProduct.url == parsed.url))
    ).scalar_one_or_none()

    if existing is None:
        product = CrawledProduct(
            source_id=source_id,
            raw_item_id=raw_item_id,
            external_id=parsed.external_id,
            url=parsed.url,
            affiliate_url=parsed.affiliate_url,
            name=parsed.name,
            brand=parsed.brand,
            price=parsed.price,
            currency=parsed.currency,
            in_stock=parsed.in_stock,
            images=parsed.images,
            specs=parsed.specs,
            category_path=parsed.category_path,
        )
        session.add(product)
        await session.flush()
        if parsed.price is not None:
            session.add(CrawledPriceHistory(product_id=product.id, price=parsed.price, currency=parsed.currency))
        return True

    price_changed = parsed.price is not None and parsed.price != existing.price
    existing.raw_item_id = raw_item_id
    existing.external_id = parsed.external_id
    existing.affiliate_url = parsed.affiliate_url
    existing.name = parsed.name
    existing.brand = parsed.brand
    existing.price = parsed.price
    existing.currency = parsed.currency
    existing.in_stock = parsed.in_stock
    existing.images = parsed.images
    existing.specs = parsed.specs
    existing.category_path = parsed.category_path
    existing.last_seen_at = datetime.now(UTC)
    if price_changed:
        session.add(CrawledPriceHistory(product_id=existing.id, price=parsed.price, currency=parsed.currency))
    return False


async def _upsert_content(session: AsyncSession, source_id, raw_item_id, parsed: ParsedContent) -> bool:
    existing = (
        await session.execute(
            select(CrawledContent).where(CrawledContent.source_id == source_id, CrawledContent.external_ref == parsed.external_ref)
        )
    ).scalar_one_or_none()

    published_at = _parse_datetime(parsed.published_at)

    if existing is None:
        session.add(
            CrawledContent(
                source_id=source_id,
                raw_item_id=raw_item_id,
                content_type=parsed.content_type,
                external_ref=parsed.external_ref,
                title=parsed.title,
                author=parsed.author,
                rating=parsed.rating,
                body=parsed.body,
                published_at=published_at,
            )
        )
        return True

    existing.raw_item_id = raw_item_id
    existing.title = parsed.title
    existing.author = parsed.author
    existing.rating = parsed.rating
    existing.body = parsed.body
    existing.published_at = published_at
    existing.fetched_at = datetime.now(UTC)
    return False


def _parse_datetime(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
