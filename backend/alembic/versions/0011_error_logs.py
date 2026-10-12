"""Operational error log for the admin console (FR-038)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0011_error_logs"
down_revision = "0010_booking_proposals_and_chat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "error_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "level",
            sa.Enum("error", "security", name="error_level", native_enum=False, create_type=False),
            nullable=False,
            server_default="error",
        ),
        sa.Column(
            "kind",
            sa.Enum(
                "server_error",
                "auth_failure",
                "forbidden",
                "rate_limited",
                "validation_error",
                name="error_kind",
                native_enum=False,
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("occurrences", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_error_logs_fingerprint", "error_logs", ["kind", "method", "path", "status_code", "message"])
    op.create_index("ix_error_logs_level_created", "error_logs", ["level", "created_at"])
    op.create_index(op.f("ix_error_logs_kind"), "error_logs", ["kind"])
    op.create_index(op.f("ix_error_logs_path"), "error_logs", ["path"])
    op.create_index(op.f("ix_error_logs_level"), "error_logs", ["level"])


def downgrade() -> None:
    op.drop_index(op.f("ix_error_logs_level"), table_name="error_logs")
    op.drop_index(op.f("ix_error_logs_path"), table_name="error_logs")
    op.drop_index(op.f("ix_error_logs_kind"), table_name="error_logs")
    op.drop_index("ix_error_logs_level_created", table_name="error_logs")
    op.drop_index("ix_error_logs_fingerprint", table_name="error_logs")
    op.drop_table("error_logs")
