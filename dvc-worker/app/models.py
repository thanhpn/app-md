import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid_col():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# Source.source_type picks which crawl strategy applies; adapter_key picks the
# concrete adapter class (see app/adapters) — kept separate because 2 sources
# of the same source_type can use different adapters (e.g. 2 e-commerce sites
# with different selector layouts still share source_type='ecommerce_product').
SOURCE_TYPES = ("ecommerce_product", "review_article", "youtube_channel")
SOURCE_STATUSES = ("active", "paused")
RUN_STATUSES = ("running", "success", "failed", "partial")
RAW_ITEM_STATUSES = ("new", "unchanged", "updated", "parse_failed")
CONTENT_TYPES = ("review_article", "product_review_comment", "youtube_video")
RELATION_TYPES = ("same_product", "similar", "accessory", "alternative")
DRAFT_SUBJECT_TYPES = ("crawled_product", "canonical_product")
DRAFT_STATUSES = ("pending", "generating", "generated", "published", "rejected")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = _uuid_col()
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    source_type: Mapped[str] = mapped_column(Enum(*SOURCE_TYPES, name="source_type"))
    adapter_key: Mapped[str] = mapped_column(String(100))
    base_url: Mapped[str] = mapped_column(Text)
    # Adapter-specific: seed_urls[], selectors{}, channel_id, max_items, etc.
    # See app/adapters/*.py docstrings for the shape each adapter_key expects.
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(Enum(*SOURCE_STATUSES, name="source_status"), default="active")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Cached IDs from apps/reviews (foreign system — no FK) set the first
    # time this source is pushed, reused on every later push so re-pushing
    # doesn't create a new category/retailer each time. See push_service.py.
    reviews_category_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviews_retailer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    runs: Mapped[list["CrawlRun"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[uuid.UUID] = _uuid_col()
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(Enum(*RUN_STATUSES, name="run_status"), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    items_found: Mapped[int] = mapped_column(default=0)
    items_new: Mapped[int] = mapped_column(default=0)
    items_updated: Mapped[int] = mapped_column(default=0)
    errors_count: Mapped[int] = mapped_column(default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped["Source"] = relationship(back_populates="runs")


class RawItem(Base):
    """Latest fetched snapshot per (source, url) — upserted every run.

    Kept so a parse failure or adapter bug can be fixed and reprocessed from
    the stored raw_content without re-hitting the source site.
    """

    __tablename__ = "raw_items"
    __table_args__ = (UniqueConstraint("source_id", "url", name="uq_raw_items_source_url"),)

    id: Mapped[uuid.UUID] = _uuid_col()
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crawl_runs.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Enum(*RAW_ITEM_STATUSES, name="raw_item_status"), default="new")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CanonicalProduct(Base):
    """Grouping entity for 'this is the same real-world product across N
    sources' — assigned later (manually via admin, or by a future matching
    job), never written by the crawler itself. Exists so price comparison /
    'similar product' features have somewhere to attach without redesigning
    the schema when that job gets built.
    """

    __tablename__ = "canonical_products"

    id: Mapped[uuid.UUID] = _uuid_col()
    name: Mapped[str] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category_hint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products: Mapped[list["CrawledProduct"]] = relationship(back_populates="canonical_product")


class CrawledProduct(Base):
    __tablename__ = "crawled_products"
    __table_args__ = (UniqueConstraint("source_id", "url", name="uq_crawled_products_source_url"),)

    id: Mapped[uuid.UUID] = _uuid_col()
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    raw_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_items.id", ondelete="SET NULL"), nullable=True)
    canonical_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str] = mapped_column(Text)
    # Trackable/commission-earning link when different from `url` (e.g.
    # Shopee affiliate offerLink) — see ParsedProduct.affiliate_url.
    affiliate_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="VND")
    in_stock: Mapped[bool | None] = mapped_column(nullable=True)
    images: Mapped[list] = mapped_column(JSON, default=list)
    specs: Mapped[dict] = mapped_column(JSON, default=dict)
    category_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Set by push_service.py after a successful push to apps/reviews — the
    # foreign Product.id there (no FK, different system/DB) and when. Presence
    # of pushed_product_id is what decides create-vs-update on the next push.
    pushed_product_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    canonical_product: Mapped["CanonicalProduct | None"] = relationship(back_populates="products")
    price_history: Mapped[list["CrawledPriceHistory"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class CrawledPriceHistory(Base):
    """1 row per observed price CHANGE (not per crawl) — same rule as
    apps/reviews.PriceHistory: only insert when price actually differs from
    the previous observation, so this stays a real price-change timeline.
    """

    __tablename__ = "crawled_price_history"

    id: Mapped[uuid.UUID] = _uuid_col()
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crawled_products.id", ondelete="CASCADE"), index=True)
    price: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(10), default="VND")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["CrawledProduct"] = relationship(back_populates="price_history")


class RelatedProductLink(Base):
    """Generic relationship graph between 2 CrawledProduct rows — the
    substrate for 'similar product' / 'same product on another site'
    features later. method records how the link was made ('manual' for now;
    'name_match'/'embedding_match' reserved for a future auto-matching job).
    """

    __tablename__ = "related_product_links"
    __table_args__ = (UniqueConstraint("product_a_id", "product_b_id", "relation_type", name="uq_related_product_links"),)

    id: Mapped[uuid.UUID] = _uuid_col()
    product_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crawled_products.id", ondelete="CASCADE"), index=True)
    product_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crawled_products.id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[str] = mapped_column(Enum(*RELATION_TYPES, name="relation_type"))
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    method: Mapped[str] = mapped_column(String(50), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrawledContent(Base):
    """Raw review/article/video material — the input a future 'xào nấu'
    (rewrite) job reads from. related_product_id is best-effort (set when
    the adapter can tell which product a piece of content is about).
    """

    __tablename__ = "crawled_content"
    __table_args__ = (UniqueConstraint("source_id", "external_ref", name="uq_crawled_content_source_ref"),)

    id: Mapped[uuid.UUID] = _uuid_col()
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    raw_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_items.id", ondelete="SET NULL"), nullable=True)
    related_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("crawled_products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    content_type: Mapped[str] = mapped_column(Enum(*CONTENT_TYPES, name="content_type"))
    external_ref: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rating: Mapped[float | None] = mapped_column(nullable=True)
    body: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentDraft(Base):
    """Queue for the future LLM 'xào nấu' job — created empty this round.
    subject_id is polymorphic (points at CrawledProduct.id or
    CanonicalProduct.id depending on subject_type) so it deliberately has no
    FK constraint; the content-gen job is responsible for resolving it.
    """

    __tablename__ = "content_drafts"

    id: Mapped[uuid.UUID] = _uuid_col()
    subject_type: Mapped[str] = mapped_column(Enum(*DRAFT_SUBJECT_TYPES, name="draft_subject_type"))
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(Enum(*DRAFT_STATUSES, name="draft_status"), default="pending")
    generated_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
