"""add_news_sync_status_columns

Revision ID: 20260616_0003
Revises: 20260616_0002
Create Date: 2026-06-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260616_0003"
down_revision: str | None = "20260616_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("news_items", sa.Column("obsidian_sync", sa.String(length=50), nullable=False, server_default="skipped"))
    op.add_column("news_items", sa.Column("git_sync", sa.String(length=50), nullable=False, server_default="skipped"))
    op.add_column("news_items", sa.Column("obsidian_path", sa.Text(), nullable=True))
    op.add_column("news_items", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("news_items", "last_synced_at")
    op.drop_column("news_items", "obsidian_path")
    op.drop_column("news_items", "git_sync")
    op.drop_column("news_items", "obsidian_sync")
