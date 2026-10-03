"""add user ownership, devices, pairings, and connectors

Revision ID: 20261001_auth_connectors
Revises: 20261001_local_file_content
"""
from alembic import op
import sqlalchemy as sa

revision = "20261001_auth_connectors"
down_revision = "20261001_local_file_content"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(320), nullable=False, unique=True), sa.Column("password_hash", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_table("auth_tokens", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False, unique=True), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])
    op.create_table("devices", sa.Column("id", sa.String(36), primary_key=True), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(), nullable=False), sa.Column("credential_hash", sa.String(64), nullable=False, unique=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("last_seen_at", sa.DateTime(timezone=True)), sa.Column("revoked_at", sa.DateTime(timezone=True)))
    op.create_index("ix_devices_owner_id", "devices", ["owner_id"])
    op.create_table("pairings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("code_hash", sa.String(64), nullable=False, unique=True), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("used_at", sa.DateTime(timezone=True)))
    op.create_index("ix_pairings_owner_id", "pairings", ["owner_id"])
    op.create_table("connectors", sa.Column("id", sa.String(36), primary_key=True), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("device_id", sa.String(36), sa.ForeignKey("devices.id", ondelete="SET NULL")), sa.Column("connector_type", sa.String(), nullable=False), sa.Column("provider", sa.String(), nullable=False), sa.Column("name", sa.String(), nullable=False), sa.Column("status", sa.String(), nullable=False), sa.Column("authentication_status", sa.String(), nullable=False), sa.Column("authorized_root", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("last_sync_at", sa.DateTime(timezone=True)), sa.Column("revoked_at", sa.DateTime(timezone=True)))
    op.create_index("ix_connectors_owner_id", "connectors", ["owner_id"])
    op.create_index("ix_connectors_device_id", "connectors", ["device_id"])
    with op.batch_alter_table("knowledge_items") as batch:
        batch.add_column(sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True))
        batch.add_column(sa.Column("connector_id", sa.String(36), sa.ForeignKey("connectors.id", ondelete="CASCADE"), nullable=True))
        batch.add_column(sa.Column("device_id", sa.String(36), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True))
        batch.add_column(sa.Column("embedding_model", sa.String(), nullable=True))
    op.create_index("ix_knowledge_items_owner_id", "knowledge_items", ["owner_id"])
    op.create_index("ix_knowledge_items_connector_id", "knowledge_items", ["connector_id"])
    op.create_index("ix_knowledge_items_device_id", "knowledge_items", ["device_id"])
    op.create_unique_constraint("uq_knowledge_items_connector_item", "knowledge_items", ["connector_id", "source_item_id"])


def downgrade() -> None:
    op.drop_constraint("uq_knowledge_items_connector_item", "knowledge_items", type_="unique")
    op.drop_index("ix_knowledge_items_device_id", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_connector_id", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_owner_id", table_name="knowledge_items")
    with op.batch_alter_table("knowledge_items") as batch:
        batch.drop_column("embedding_model")
        batch.drop_column("device_id")
        batch.drop_column("connector_id")
        batch.drop_column("owner_id")
    op.drop_table("connectors")
    op.drop_table("pairings")
    op.drop_table("devices")
    op.drop_table("auth_tokens")
    op.drop_table("users")
