"""Store the selected mode with each search history entry."""
from alembic import op
import sqlalchemy as sa

revision = "20261007_search_history_mode"
down_revision = "20261006_activity_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "search_history",
        sa.Column("mode", sa.String(16), nullable=False, server_default="ask"),
    )


def downgrade() -> None:
    op.drop_column("search_history", "mode")
