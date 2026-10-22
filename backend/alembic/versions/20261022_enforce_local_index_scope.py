"""Require owner, connector, and device scope for local index records.

Revision ID: 20261022_local_scope
Revises: 20261022_drop_raw_content
Create Date: 2026-10-22
"""
from alembic import op


revision = "20261022_local_scope"
down_revision = "20261022_drop_raw_content"
branch_labels = None
depends_on = None


def upgrade() -> None:
	# Legacy local records without an owner/connector/device cannot be safely
	# attributed, so remove their derived index representation.
	op.execute(
		"DELETE FROM knowledge_items WHERE source = 'local' AND "
		"(owner_id IS NULL OR connector_id IS NULL OR device_id IS NULL)"
	)
	op.create_check_constraint(
		"ck_local_knowledge_items_have_scope",
		"knowledge_items",
		"source <> 'local' OR (owner_id IS NOT NULL AND connector_id IS NOT NULL AND device_id IS NOT NULL)",
	)


def downgrade() -> None:
	op.drop_constraint("ck_local_knowledge_items_have_scope", "knowledge_items", type_="check")
