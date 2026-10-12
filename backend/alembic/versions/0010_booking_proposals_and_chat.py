"""Propose-a-time negotiation fields + per-booking chat."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0010_booking_proposals_and_chat"
down_revision = "0009_rename_expert_to_consultant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Bookings: proposal/negotiation fields
    op.alter_column(
        "bookings",
        "slot_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.add_column(
        "bookings",
        sa.Column(
            "origin",
            sa.Enum("slot", "proposal", name="booking_origin", native_enum=False, create_type=False),
            server_default="slot",
            nullable=False,
        ),
    )
    op.add_column(
        "bookings",
        sa.Column("last_proposed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_bookings_last_proposed_by_id",
        "bookings",
        "users",
        ["last_proposed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Per-booking chat
    op.create_table(
        "booking_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_booking_messages_booking_id", "booking_messages", ["booking_id"])
    op.create_index("ix_booking_messages_sender_id", "booking_messages", ["sender_id"])
    op.create_index("ix_booking_messages_booking_created", "booking_messages", ["booking_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_booking_messages_booking_created", table_name="booking_messages")
    op.drop_index("ix_booking_messages_sender_id", table_name="booking_messages")
    op.drop_index("ix_booking_messages_booking_id", table_name="booking_messages")
    op.drop_table("booking_messages")

    op.drop_constraint("fk_bookings_last_proposed_by_id", "bookings", type_="foreignkey")
    op.drop_column("bookings", "last_proposed_by_id")
    op.drop_column("bookings", "origin")
    op.alter_column(
        "bookings",
        "slot_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
