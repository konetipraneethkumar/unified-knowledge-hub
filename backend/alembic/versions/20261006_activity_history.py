"""Persist user search and connector sync activity."""
from alembic import op
import sqlalchemy as sa

revision = "20261006_activity_history"
down_revision = "20261005_source_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_search_history_owner_id", "search_history", ["owner_id"])
    op.create_index("ix_search_history_owner_created", "search_history", ["owner_id", "created_at"])
    op.create_table(
        "connector_sync_activity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connector_id", sa.String(36), sa.ForeignKey("connectors.id", ondelete="SET NULL")),
        sa.Column("connector_name", sa.String(), nullable=False),
        sa.Column("connector_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("processed", sa.Integer()),
        sa.Column("skipped", sa.Integer()),
        sa.Column("failed", sa.Integer()),
        sa.Column("deleted", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_connector_sync_activity_owner_id", "connector_sync_activity", ["owner_id"])
    op.create_index("ix_connector_sync_activity_connector_id", "connector_sync_activity", ["connector_id"])
    op.create_index("ix_sync_activity_owner_created", "connector_sync_activity", ["owner_id", "created_at"])


def downgrade() -> None:
    op.drop_table("connector_sync_activity")
    op.drop_table("search_history")
