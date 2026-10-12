"""Add event-driven notification types (new_user, new_reading, new_question)."""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_notification_event_types"
down_revision = "0007_booking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ADD VALUE is transaction-safe for new notification types.
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'new_user'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'new_reading'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'new_question'")


def downgrade() -> None:
    pass
