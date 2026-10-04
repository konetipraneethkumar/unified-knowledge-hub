"""add JWT refresh, Google identity, OAuth state, and encrypted connector credentials.

Revision ID: 20261004_auth_oauth
Revises: 20261003_connector_item_unique
"""
from alembic import op
import sqlalchemy as sa

revision = "20261004_auth_oauth"
down_revision = "20261003_connector_item_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_auth_tokens_user_id", table_name="auth_tokens")
    op.drop_table("auth_tokens")
    with op.batch_alter_table("users") as batch:
        batch.alter_column("password_hash", existing_type=sa.String(), nullable=True)
        batch.add_column(sa.Column("display_name", sa.String(255)))
        batch.add_column(sa.Column("avatar_url", sa.Text()))
        batch.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        batch.add_column(sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_table("refresh_tokens", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_hash", sa.String(64), unique=True, nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("replaced_by_token_id", sa.Integer(), sa.ForeignKey("refresh_tokens.id")))
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_table("oauth_accounts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("provider", sa.String(64), nullable=False), sa.Column("provider_subject", sa.String(255), nullable=False), sa.Column("email_at_link_time", sa.String(320)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.UniqueConstraint("provider", "provider_subject", name="uq_oauth_account_provider_subject"))
    op.create_index("ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"])
    op.create_table("oauth_states", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("state_hash", sa.String(64), unique=True, nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")), sa.Column("purpose", sa.String(64), nullable=False), sa.Column("nonce", sa.String(255)), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("used_at", sa.DateTime(timezone=True)))
    op.create_index("ix_oauth_states_user_id", "oauth_states", ["user_id"])
    with op.batch_alter_table("connectors") as batch:
        batch.add_column(sa.Column("external_account_id", sa.String(255)))
        batch.add_column(sa.Column("scopes", sa.Text()))
    op.create_table("connector_credentials", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("connector_id", sa.String(36), sa.ForeignKey("connectors.id", ondelete="CASCADE"), unique=True, nullable=False), sa.Column("encrypted_access_token", sa.Text()), sa.Column("encrypted_refresh_token", sa.Text()), sa.Column("token_expires_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))


def downgrade() -> None:
    op.drop_table("connector_credentials")
    with op.batch_alter_table("connectors") as batch: batch.drop_column("scopes"); batch.drop_column("external_account_id")
    op.drop_table("oauth_states"); op.drop_table("oauth_accounts"); op.drop_table("refresh_tokens")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("updated_at"); batch.drop_column("is_verified"); batch.drop_column("is_active"); batch.drop_column("avatar_url"); batch.drop_column("display_name"); batch.alter_column("password_hash", existing_type=sa.String(), nullable=False)
    op.create_table("auth_tokens", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_hash", sa.String(64), unique=True, nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])
