"""add local file metadata and source item uniqueness

Revision ID: 20260930_local_file_metadata
Revises: 8414841d9cb1
Create Date: 2026-09-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260930_local_file_metadata"
down_revision: Union[str, Sequence[str], None] = "8414841d9cb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.add_column(
		"knowledge_items", sa.Column("file_extension", sa.String(), nullable=True)
	)
	op.add_column(
		"knowledge_items", sa.Column("file_size_bytes", sa.Integer(), nullable=True)
	)
	op.add_column(
		"knowledge_items",
		sa.Column("file_created_at", sa.DateTime(timezone=True), nullable=True),
	)
	op.create_index(
		"uq_knowledge_items_source_item",
		"knowledge_items",
		["source", "source_item_id"],
		unique=True,
	)


def downgrade() -> None:
	op.drop_index("uq_knowledge_items_source_item", table_name="knowledge_items")
	op.drop_column("knowledge_items", "file_created_at")
	op.drop_column("knowledge_items", "file_size_bytes")
	op.drop_column("knowledge_items", "file_extension")