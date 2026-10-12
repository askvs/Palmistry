"""recommendation_records + recommendation_events (Module 9, FR-034, TASK-012)."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0004_recommendations"
down_revision: Union[str, None] = "0003_roles_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    recommendation_type = sa.Enum(
        "personal_growth", "relationship", "career", "goal_alignment",
        "spiritual_development", name="recommendation_type",
    )
    recommendation_status = sa.Enum(
        "new", "accepted", "dismissed", "completed", name="recommendation_status",
    )
    event_type = sa.Enum(
        "shown", "accepted", "dismissed", "completed", "rated",
        name="recommendation_event_type",
    )

    op.create_table(
        "recommendation_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "reading_id",
            UUID(as_uuid=True),
            sa.ForeignKey("readings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("batch_id", UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", sa.String(length=80), nullable=False),
        sa.Column("rec_type", recommendation_type, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", recommendation_status, nullable=False, server_default="new"),
        sa.Column("feedback_rating", sa.Integer(), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_recommendation_records_user_id", "recommendation_records", ["user_id"])
    op.create_index("ix_recommendation_records_batch_id", "recommendation_records", ["batch_id"])
    op.create_index("ix_recommendation_records_item_id", "recommendation_records", ["item_id"])
    op.create_index("ix_recommendation_records_rec_type", "recommendation_records", ["rec_type"])
    op.create_index("ix_recommendation_records_status", "recommendation_records", ["status"])

    op.create_table(
        "recommendation_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "record_id",
            UUID(as_uuid=True),
            sa.ForeignKey("recommendation_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_recommendation_events_record_id", "recommendation_events", ["record_id"])
    op.create_index("ix_recommendation_events_user_id", "recommendation_events", ["user_id"])
    op.create_index("ix_recommendation_events_event_type", "recommendation_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("recommendation_events")
    op.drop_table("recommendation_records")
    for name in (
        "recommendation_event_type",
        "recommendation_status",
        "recommendation_type",
    ):
        op.execute(f"DROP TYPE IF EXISTS {name}")
