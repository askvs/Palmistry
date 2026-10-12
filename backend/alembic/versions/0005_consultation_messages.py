"""consultation_messages thread table (FR-006, two-way seeker/consultant messaging)."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0005_consultation_messages"
down_revision: Union[str, None] = "0004_recommendations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consultation_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "consultation_id",
            UUID(as_uuid=True),
            sa.ForeignKey("consultations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text(), nullable=False),
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
    op.create_index(
        "ix_consultation_messages_consultation_id",
        "consultation_messages",
        ["consultation_id"],
    )
    op.create_index(
        "ix_consultation_messages_sender_id",
        "consultation_messages",
        ["sender_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_consultation_messages_sender_id", table_name="consultation_messages"
    )
    op.drop_index(
        "ix_consultation_messages_consultation_id", table_name="consultation_messages"
    )
    op.drop_table("consultation_messages")
