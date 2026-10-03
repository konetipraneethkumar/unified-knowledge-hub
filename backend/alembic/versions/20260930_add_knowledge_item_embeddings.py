"""store knowledge item embeddings separately

Revision ID: 20260930_embeddings
Revises: 20260930_local_file_metadata
Create Date: 2026-09-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "20260930_embeddings"
down_revision: Union[str, Sequence[str], None] = "20260930_local_file_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	if op.get_context().dialect.name == "postgresql":
		op.execute("CREATE EXTENSION IF NOT EXISTS vector")
	op.create_table(
		"knowledge_item_embeddings",
		sa.Column(
			"item_id",
			sa.Integer(),
			sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
			primary_key=True,
		),
		sa.Column("embedding", Vector(), nullable=False),
	)


def downgrade() -> None:
	op.drop_table("knowledge_item_embeddings")