"""Rename the booking module's "expert" vocabulary to "consultant"."""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0009_rename_expert_to_consultant"
down_revision = "0008_notification_event_types"
branch_labels = None
depends_on = None


# (old_name, new_name) index renames.
INDEX_RENAMES = [
    ("ix_expert_profiles_user_id", "ix_consultant_profiles_user_id"),
    ("ix_expert_profiles_accepting", "ix_consultant_profiles_accepting"),
    ("ix_availability_rules_expert_id", "ix_availability_rules_consultant_id"),
    ("ix_availability_rules_expert", "ix_availability_rules_consultant"),
    ("ix_availability_slots_expert_id", "ix_availability_slots_consultant_id"),
    ("ix_availability_slots_expert_start", "ix_availability_slots_consultant_start"),
    ("ix_bookings_expert_id", "ix_bookings_consultant_id"),
    ("ix_bookings_expert_start", "ix_bookings_consultant_start"),
    ("ix_session_feedbacks_expert_id", "ix_session_feedbacks_consultant_id"),
    ("ix_session_feedbacks_expert", "ix_session_feedbacks_consultant"),
    (
        "ix_expert_calendar_connections_expert_id",
        "ix_consultant_calendar_connections_consultant_id",
    ),
]

# (table, old_constraint, new_constraint) renames.
CONSTRAINT_RENAMES = [
    ("consultant_profiles", "uq_expert_profiles_user_id", "uq_consultant_profiles_user_id"),
    (
        "consultant_calendar_connections",
        "uq_expert_calendar_connection",
        "uq_consultant_calendar_connection",
    ),
]

# (table, old_column, new_column) renames — all expert_id -> consultant_id.
COLUMN_RENAMES = [
    ("availability_rules", "expert_id", "consultant_id"),
    ("availability_slots", "expert_id", "consultant_id"),
    ("bookings", "expert_id", "consultant_id"),
    ("session_feedbacks", "expert_id", "consultant_id"),
    ("consultant_calendar_connections", "expert_id", "consultant_id"),
]


def upgrade() -> None:
    # Tables first so later column/constraint renames target the new names.
    op.rename_table("expert_profiles", "consultant_profiles")
    op.rename_table("expert_calendar_connections", "consultant_calendar_connections")

    for table, old, new in COLUMN_RENAMES:
        op.alter_column(table, old, new_column_name=new)

    for old, new in INDEX_RENAMES:
        op.execute(f'ALTER INDEX "{old}" RENAME TO "{new}"')

    for table, old, new in CONSTRAINT_RENAMES:
        op.execute(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{old}" TO "{new}"')


def downgrade() -> None:
    for table, old, new in CONSTRAINT_RENAMES:
        op.execute(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{new}" TO "{old}"')

    for old, new in INDEX_RENAMES:
        op.execute(f'ALTER INDEX "{new}" RENAME TO "{old}"')

    for table, old, new in COLUMN_RENAMES:
        # `table` already uses the post-upgrade name for the two renamed tables.
        op.alter_column(table, new, new_column_name=old)

    op.rename_table("consultant_calendar_connections", "expert_calendar_connections")
    op.rename_table("consultant_profiles", "expert_profiles")
