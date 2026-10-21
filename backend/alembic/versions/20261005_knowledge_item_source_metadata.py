"""preserve source metadata on knowledge items

Revision ID: 20261005_source_metadata
Revises: 20261004_auth_oauth
"""
from alembic import op
import sqlalchemy as sa

revision = "20261005_source_metadata"
down_revision = "20261004_auth_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_items", sa.Column("parent_location", sa.Text()))
    op.add_column("knowledge_items", sa.Column("web_url", sa.Text()))
    op.add_column("knowledge_items", sa.Column("file_path", sa.Text()))
    op.add_column("knowledge_items", sa.Column("source_metadata", sa.JSON()))


def downgrade() -> None:
    op.drop_column("knowledge_items", "source_metadata")
    op.drop_column("knowledge_items", "file_path")
    op.drop_column("knowledge_items", "web_url")
    op.drop_column("knowledge_items", "parent_location")
