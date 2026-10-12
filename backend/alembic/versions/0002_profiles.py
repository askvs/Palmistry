"""profiles + profile_interests + profile_goals (TASK-004, FR-005)."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002_profiles"
down_revision: Union[str, None] = "0001_auth_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("age_group", sa.String(length=10), nullable=True),
        sa.Column("avatar_key", sa.String(length=64), nullable=True),
        sa.Column(
            "default_deck", sa.String(length=80), nullable=False,
            server_default="Rider-Waite-Smith",
        ),
        sa.Column(
            "favorite_spread", sa.String(length=40), nullable=False,
            server_default="Three Card",
        ),
        sa.Column("tone", sa.String(length=20), nullable=False, server_default="Gentle"),
        sa.Column(
            "notify_daily_guidance", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("notify_reminders", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notify_sms", sa.Boolean(), nullable=False, server_default=sa.false()),
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
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"], unique=True)

    op.create_table(
        "profile_interests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "profile_id",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("interest", sa.String(length=60), nullable=False),
        sa.UniqueConstraint("profile_id", "interest", name="uq_profile_interest"),
    )
    op.create_index(
        "ix_profile_interests_profile_id", "profile_interests", ["profile_id"]
    )
    op.create_index("ix_profile_interests_interest", "profile_interests", ["interest"])

    op.create_table(
        "profile_goals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "profile_id",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
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
    )
    op.create_index("ix_profile_goals_profile_id", "profile_goals", ["profile_id"])

    op.execute(
        "INSERT INTO profiles (id, user_id) "
        "SELECT gen_random_uuid(), id FROM users "
        "WHERE id NOT IN (SELECT user_id FROM profiles)"
    )


def downgrade() -> None:
    op.drop_index("ix_profile_goals_profile_id", table_name="profile_goals")
    op.drop_table("profile_goals")
    op.drop_index("ix_profile_interests_interest", table_name="profile_interests")
    op.drop_index("ix_profile_interests_profile_id", table_name="profile_interests")
    op.drop_table("profile_interests")
    op.drop_index("ix_profiles_user_id", table_name="profiles")
    op.drop_table("profiles")
