"""create_news_items_table

Revision ID: 20260616_0001
Revises:
Create Date: 2026-06-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260616_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("importance", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("ecosystem", sa.String(length=150), nullable=True),
        sa.Column("companies", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_news_items_id"), "news_items", ["id"], unique=False)
    op.create_index(op.f("ix_news_items_date"), "news_items", ["date"], unique=False)
    op.create_index(op.f("ix_news_items_importance"), "news_items", ["importance"], unique=False)
    op.create_index(op.f("ix_news_items_category"), "news_items", ["category"], unique=False)
    op.create_index(op.f("ix_news_items_ecosystem"), "news_items", ["ecosystem"], unique=False)
    op.create_index(op.f("ix_news_items_source"), "news_items", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_news_items_source"), table_name="news_items")
    op.drop_index(op.f("ix_news_items_ecosystem"), table_name="news_items")
    op.drop_index(op.f("ix_news_items_category"), table_name="news_items")
    op.drop_index(op.f("ix_news_items_importance"), table_name="news_items")
    op.drop_index(op.f("ix_news_items_date"), table_name="news_items")
    op.drop_index(op.f("ix_news_items_id"), table_name="news_items")
    op.drop_table("news_items")
