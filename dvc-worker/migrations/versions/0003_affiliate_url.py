"""affiliate_url on crawled_products

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-03

"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("crawled_products", sa.Column("affiliate_url", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("crawled_products", "affiliate_url")
