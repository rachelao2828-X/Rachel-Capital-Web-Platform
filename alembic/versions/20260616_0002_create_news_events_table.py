"""create_news_events_table

Revision ID: 20260616_0002
Revises: 20260616_0001
Create Date: 2026-06-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260616_0002"
down_revision: str | None = "20260616_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("news_item_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("ecosystem", sa.String(length=150), nullable=True),
        sa.Column("companies", sa.JSON(), nullable=False),
        sa.Column("impact", sa.Text(), nullable=True),
        sa.Column("importance", sa.String(length=32), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["news_item_id"], ["news_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_news_events_id"), "news_events", ["id"], unique=False)
    op.create_index(op.f("ix_news_events_news_item_id"), "news_events", ["news_item_id"], unique=False)
    op.create_index(op.f("ix_news_events_ecosystem"), "news_events", ["ecosystem"], unique=False)
    op.create_index(op.f("ix_news_events_importance"), "news_events", ["importance"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_news_events_importance"), table_name="news_events")
    op.drop_index(op.f("ix_news_events_ecosystem"), table_name="news_events")
    op.drop_index(op.f("ix_news_events_news_item_id"), table_name="news_events")
    op.drop_index(op.f("ix_news_events_id"), table_name="news_events")
    op.drop_table("news_events")
