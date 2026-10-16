"""Remove the Google Calendar integration (Meet links are shared manually)."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0013_remove_google_calendar"
down_revision = "0012_custom_spreads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Per-consultant OAuth connections to Google Calendar.
    op.drop_index(
        "ix_consultant_calendar_connections_consultant_id",
        table_name="consultant_calendar_connections",
    )
    op.drop_table("consultant_calendar_connections")

    # Calendar bookkeeping on bookings (the manual `meet_link` stays).
    op.drop_column("bookings", "google_event_id")
    op.drop_column("bookings", "google_calendar_id")
    op.drop_column("bookings", "meet_code")
    op.drop_column("bookings", "calendar_sync_status")
    op.drop_column("bookings", "calendar_synced_at")
    op.drop_column("bookings", "calendar_error")

    # The original enum type was superseded by a varchar column; clean it up.
    op.execute("DROP TYPE IF EXISTS booking_calendar_sync_status")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE booking_calendar_sync_status AS ENUM "
        "('disabled', 'not_created', 'created', 'failed', 'cancelled')"
    )

    op.add_column(
        "bookings",
        sa.Column("google_event_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("google_calendar_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "bookings", sa.Column("meet_code", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "bookings",
        sa.Column(
            "calendar_sync_status",
            sa.Enum(
                "disabled",
                "not_created",
                "created",
                "failed",
                "cancelled",
                name="booking_calendar_sync_status",
                native_enum=False,
                create_type=False,
            ),
            server_default="not_created",
            nullable=False,
        ),
    )
    op.add_column(
        "bookings",
        sa.Column("calendar_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("bookings", sa.Column("calendar_error", sa.Text(), nullable=True))

    op.create_table(
        "consultant_calendar_connections",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "consultant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("consultant_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("google_email", sa.String(length=320), nullable=True),
        sa.Column("google_account_id", sa.String(length=64), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column(
            "access_token_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "calendar_id",
            sa.String(length=255),
            server_default="primary",
            nullable=False,
        ),
        sa.Column(
            "timezone", sa.String(length=64), server_default="UTC", nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "connected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultant_id", name="uq_consultant_calendar_connection"
        ),
    )
    op.create_index(
        "ix_consultant_calendar_connections_consultant_id",
        "consultant_calendar_connections",
        ["consultant_id"],
        unique=True,
    )
