"""scope source item uniqueness to a connector.

Revision ID: 20261003_connector_item_unique
Revises: 20261001_auth_connectors
Create Date: 2026-10-03
"""
from alembic import op


revision = "20261003_connector_item_unique"
down_revision = "20261001_auth_connectors"
branch_labels = None
depends_on = None


def upgrade() -> None:
	# The original discovery index pre-dated connectors and incorrectly made a
	# source item globally unique. Source identity is connector-scoped.
	op.drop_index("uq_knowledge_items_source_item", table_name="knowledge_items")


def downgrade() -> None:
	op.create_index(
		"uq_knowledge_items_source_item",
		"knowledge_items",
		["source", "source_item_id"],
		unique=True,
	)
