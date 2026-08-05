"""push tracking fields for reviews-web integration

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-02

"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("reviews_category_id", sa.String(64), nullable=True))
    op.add_column("sources", sa.Column("reviews_retailer_id", sa.String(64), nullable=True))
    op.add_column("crawled_products", sa.Column("pushed_product_id", sa.String(64), nullable=True))
    op.add_column("crawled_products", sa.Column("pushed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("crawled_products", "pushed_at")
    op.drop_column("crawled_products", "pushed_product_id")
    op.drop_column("sources", "reviews_retailer_id")
    op.drop_column("sources", "reviews_category_id")
