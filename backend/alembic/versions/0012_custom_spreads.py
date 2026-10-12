"""Reader-authored tarot spreads (Tarot Reader role: create spreads)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0012_custom_spreads"
down_revision = "0011_error_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "custom_spreads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=60), nullable=False, server_default="custom"),
        sa.Column("positions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("card_count", sa.Integer(), nullable=False),
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="private",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
    )
    op.create_index(op.f("ix_custom_spreads_owner_id"), "custom_spreads", ["owner_id"])
    op.create_index("ix_custom_spreads_owner_name", "custom_spreads", ["owner_id", "name"])


def downgrade() -> None:
    op.drop_index("ix_custom_spreads_owner_name", table_name="custom_spreads")
    op.drop_index(op.f("ix_custom_spreads_owner_id"), table_name="custom_spreads")
    op.drop_table("custom_spreads")
