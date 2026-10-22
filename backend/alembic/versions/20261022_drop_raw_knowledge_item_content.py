"""Remove persisted extracted document text from the derived index.

Revision ID: 20261022_drop_raw_content
Revises: 20261003_connector_item_unique
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa


revision = "20261022_drop_raw_content"
down_revision = "20261003_connector_item_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.drop_column("knowledge_items", "content")


def downgrade() -> None:
	op.add_column("knowledge_items", sa.Column("content", sa.Text(), nullable=True))
