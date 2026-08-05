"""init schema

Revision ID: 0001
Revises:
Create Date: 2026-08-02

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False, unique=True),
        sa.Column("source_type", sa.Enum("ecommerce_product", "review_article", "youtube_channel", name="source_type"), nullable=False),
        sa.Column("adapter_key", sa.String(100), nullable=False),
        sa.Column("base_url", sa.Text, nullable=False),
        sa.Column("config", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("schedule_cron", sa.String(100), nullable=True),
        sa.Column("status", sa.Enum("active", "paused", name="source_status"), nullable=False, server_default="active"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sources_slug", "sources", ["slug"])

    op.create_table(
        "crawl_runs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", pg.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("running", "success", "failed", "partial", name="run_status"), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("items_found", sa.Integer, nullable=False, server_default="0"),
        sa.Column("items_new", sa.Integer, nullable=False, server_default="0"),
        sa.Column("items_updated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("errors_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text, nullable=True),
    )
    op.create_index("ix_crawl_runs_source_id", "crawl_runs", ["source_id"])

    op.create_table(
        "raw_items",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", pg.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("crawl_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("raw_content", sa.Text, nullable=False),
        sa.Column("status", sa.Enum("new", "unchanged", "updated", "parse_failed", name="raw_item_status"), nullable=False, server_default="new"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_id", "url", name="uq_raw_items_source_url"),
    )
    op.create_index("ix_raw_items_source_id", "raw_items", ["source_id"])

    op.create_table(
        "canonical_products",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("brand", sa.String(200), nullable=True),
        sa.Column("category_hint", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "crawled_products",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", pg.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_item_id", pg.UUID(as_uuid=True), sa.ForeignKey("raw_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("canonical_product_id", pg.UUID(as_uuid=True), sa.ForeignKey("canonical_products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_id", sa.String(200), nullable=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("brand", sa.String(200), nullable=True),
        sa.Column("price", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="VND"),
        sa.Column("in_stock", sa.Boolean, nullable=True),
        sa.Column("images", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("specs", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("category_path", sa.String(500), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_id", "url", name="uq_crawled_products_source_url"),
    )
    op.create_index("ix_crawled_products_source_id", "crawled_products", ["source_id"])
    op.create_index("ix_crawled_products_canonical_product_id", "crawled_products", ["canonical_product_id"])

    op.create_table(
        "crawled_price_history",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", pg.UUID(as_uuid=True), sa.ForeignKey("crawled_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="VND"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crawled_price_history_product_id", "crawled_price_history", ["product_id"])

    op.create_table(
        "related_product_links",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_a_id", pg.UUID(as_uuid=True), sa.ForeignKey("crawled_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_b_id", pg.UUID(as_uuid=True), sa.ForeignKey("crawled_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.Enum("same_product", "similar", "accessory", "alternative", name="relation_type"), nullable=False),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("method", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("product_a_id", "product_b_id", "relation_type", name="uq_related_product_links"),
    )
    op.create_index("ix_related_product_links_product_a_id", "related_product_links", ["product_a_id"])
    op.create_index("ix_related_product_links_product_b_id", "related_product_links", ["product_b_id"])

    op.create_table(
        "crawled_content",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", pg.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_item_id", pg.UUID(as_uuid=True), sa.ForeignKey("raw_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("related_product_id", pg.UUID(as_uuid=True), sa.ForeignKey("crawled_products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_type", sa.Enum("review_article", "product_review_comment", "youtube_video", name="content_type"), nullable=False),
        sa.Column("external_ref", sa.Text, nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("rating", sa.Float, nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_id", "external_ref", name="uq_crawled_content_source_ref"),
    )
    op.create_index("ix_crawled_content_source_id", "crawled_content", ["source_id"])
    op.create_index("ix_crawled_content_related_product_id", "crawled_content", ["related_product_id"])

    op.create_table(
        "content_drafts",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject_type", sa.Enum("crawled_product", "canonical_product", name="draft_subject_type"), nullable=False),
        sa.Column("subject_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Enum("pending", "generating", "generated", "published", "rejected", name="draft_status"), nullable=False, server_default="pending"),
        sa.Column("generated_title", sa.String(500), nullable=True),
        sa.Column("generated_body", sa.Text, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("content_drafts")
    op.drop_table("crawled_content")
    op.drop_table("related_product_links")
    op.drop_table("crawled_price_history")
    op.drop_table("crawled_products")
    op.drop_table("canonical_products")
    op.drop_table("raw_items")
    op.drop_table("crawl_runs")
    op.drop_table("sources")
    for enum_name in (
        "draft_status",
        "draft_subject_type",
        "content_type",
        "relation_type",
        "raw_item_status",
        "run_status",
        "source_status",
        "source_type",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
