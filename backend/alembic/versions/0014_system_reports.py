"""System reports: analysis duration column and API latency samples table."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0014_system_reports"
down_revision = "0013_remove_google_calendar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Measured generation duration for palm/tarot readings.
    op.add_column("readings", sa.Column("duration_ms", sa.Float(), nullable=True))

    # Buffered API latency samples flushed from the monitoring middleware.
    op.create_table(
        "performance_samples",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "sampled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_performance_samples_sampled_at", "performance_samples", ["sampled_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_performance_samples_sampled_at", table_name="performance_samples")
    op.drop_table("performance_samples")
    op.drop_column("readings", "duration_ms")
