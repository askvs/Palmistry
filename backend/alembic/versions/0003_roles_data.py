"""readings + consultations + audit_logs (FR-002, FR-003, FR-006, FR-007)."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0003_roles_data"
down_revision: Union[str, None] = "0002_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    reading_type = sa.Enum("palm", "tarot", name="reading_type")
    reading_status = sa.Enum("pending", "completed", name="reading_status")
    consultation_status = sa.Enum("open", "in_review", "resolved", name="consultation_status")

    op.create_table(
        "readings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", reading_type, nullable=False),
        sa.Column("status", reading_status, nullable=False, server_default="pending"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("result", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_readings_user_id", "readings", ["user_id"])
    op.create_index("ix_readings_type", "readings", ["type"])
    op.create_index("ix_readings_status", "readings", ["status"])

    op.create_table(
        "consultations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "consultant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("guidance", sa.Text(), nullable=True),
        sa.Column("status", consultation_status, nullable=False, server_default="open"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_consultations_user_id", "consultations", ["user_id"])
    op.create_index("ix_consultations_consultant_id", "consultations", ["consultant_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "actor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target", sa.String(length=200), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_consultations_consultant_id", table_name="consultations")
    op.drop_index("ix_consultations_user_id", table_name="consultations")
    op.drop_table("consultations")
    op.drop_index("ix_readings_status", table_name="readings")
    op.drop_index("ix_readings_type", table_name="readings")
    op.drop_index("ix_readings_user_id", table_name="readings")
    op.drop_table("readings")
    sa.Enum(name="consultation_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reading_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reading_type").drop(op.get_bind(), checkfirst=True)
