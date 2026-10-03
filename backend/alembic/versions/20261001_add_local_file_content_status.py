"""store extracted local document text and processing state

Revision ID: 20261001_local_file_content
Revises: 20260930_embeddings
Create Date: 2026-10-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261001_local_file_content"
down_revision: Union[str, Sequence[str], None] = "20260930_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.add_column("knowledge_items", sa.Column("content", sa.Text(), nullable=True))
	op.add_column(
		"knowledge_items",
		sa.Column("processing_status", sa.String(), nullable=False, server_default="pending"),
	)
	op.add_column(
		"knowledge_items", sa.Column("processing_error", sa.Text(), nullable=True)
	)
def downgrade() -> None:
	op.drop_column("knowledge_items", "processing_error")
	op.drop_column("knowledge_items", "processing_status")
	op.drop_column("knowledge_items", "content")