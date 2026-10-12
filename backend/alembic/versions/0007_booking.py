"""Add live consultation & booking tables."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0007_booking'
down_revision = '0006_notifications'
branch_labels = None
depends_on = None


# Notification categories added for the booking module.
BOOKING_NOTIFICATION_TYPES = (
    "booking_requested",
    "booking_accepted",
    "booking_rejected",
    "booking_cancelled",
    "booking_reminder",
    "booking_completed",
)


def upgrade() -> None:
    # Enums
    op.execute(
        "CREATE TYPE booking_status AS ENUM "
        "('pending', 'accepted', 'rejected', 'completed', 'cancelled')"
    )
    op.execute(
        "CREATE TYPE booking_slot_status AS ENUM "
        "('available', 'booked', 'blocked', 'cancelled')"
    )
    op.execute(
        "CREATE TYPE booking_calendar_sync_status AS ENUM "
        "('disabled', 'not_created', 'created', 'failed', 'cancelled')"
    )
    op.execute(
        "CREATE TYPE booking_note_visibility AS ENUM ('private', 'shared')"
    )

    # Extend the existing notification enum with booking categories.
    for value in BOOKING_NOTIFICATION_TYPES:
        op.execute(
            f"ALTER TYPE notification_type ADD VALUE IF NOT EXISTS '{value}'"
        )

    # Expert profiles
    op.create_table(
        'expert_profiles',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('headline', sa.String(length=160), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('specializations', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('modalities', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('languages', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('years_experience', sa.Integer(), server_default='0', nullable=False),
        sa.Column('session_rate', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('session_duration_minutes', sa.Integer(), server_default='60', nullable=False),
        sa.Column('buffer_minutes', sa.Integer(), server_default='15', nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('is_accepting_bookings', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('total_sessions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('avg_rating', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('review_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_expert_profiles_user_id'),
    )
    op.create_index('ix_expert_profiles_user_id', 'expert_profiles', ['user_id'], unique=True)
    op.create_index('ix_expert_profiles_accepting', 'expert_profiles', ['is_accepting_bookings'])

    # Recurring availability rules
    op.create_table(
        'availability_rules',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('expert_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('expert_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('weekday', sa.SmallInteger(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('slot_duration_minutes', sa.Integer(), server_default='60', nullable=False),
        sa.Column('buffer_minutes', sa.Integer(), server_default='15', nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_until', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('expert_id', 'weekday', 'start_time', 'end_time', 'effective_from', name='uq_availability_rule_window'),
    )
    op.create_index('ix_availability_rules_expert_id', 'availability_rules', ['expert_id'])
    op.create_index('ix_availability_rules_expert', 'availability_rules', ['expert_id', 'is_active'])

    # Concrete availability slots
    op.create_table(
        'availability_slots',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('expert_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('expert_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('availability_rules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('status', sa.Enum('available', 'booked', 'blocked', 'cancelled', name='booking_slot_status', native_enum=False, create_type=False), server_default='available', nullable=False),
        # Booking link; FK added after both tables exist.
        sa.Column('booking_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_availability_slots_expert_id', 'availability_slots', ['expert_id'])
    op.create_index('ix_availability_slots_rule_id', 'availability_slots', ['rule_id'])
    op.create_index('ix_availability_slots_booking_id', 'availability_slots', ['booking_id'])
    op.create_index('ix_availability_slots_start_time', 'availability_slots', ['start_time'])
    op.create_index('ix_availability_slots_expert_start', 'availability_slots', ['expert_id', 'start_time'])
    op.create_index('ix_availability_slots_status', 'availability_slots', ['expert_id', 'status', 'start_time'])

    # Bookings
    op.create_table(
        'bookings',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        # `slot_id` -> availability_slots.id; FK added below (mutually referential).
        sa.Column('slot_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expert_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('expert_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'accepted', 'rejected', 'completed', 'cancelled', name='booking_status', native_enum=False, create_type=False), server_default='pending', nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), server_default='60', nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('google_event_id', sa.String(length=255), nullable=True),
        sa.Column('google_calendar_id', sa.String(length=255), nullable=True),
        sa.Column('meet_link', sa.String(length=500), nullable=True),
        sa.Column('meet_code', sa.String(length=64), nullable=True),
        sa.Column('calendar_sync_status', sa.Enum('disabled', 'not_created', 'created', 'failed', 'cancelled', name='booking_calendar_sync_status', native_enum=False, create_type=False), server_default='not_created', nullable=False),
        sa.Column('calendar_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calendar_error', sa.Text(), nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('short_reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('cancelled_by_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bookings_slot_id', 'bookings', ['slot_id'])
    op.create_index('ix_bookings_expert_id', 'bookings', ['expert_id'])
    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'])
    op.create_index('ix_bookings_cancelled_by_id', 'bookings', ['cancelled_by_id'])
    op.create_index('ix_bookings_start_time', 'bookings', ['start_time'])
    op.create_index('ix_bookings_expert_start', 'bookings', ['expert_id', 'start_time'])
    op.create_index('ix_bookings_user_start', 'bookings', ['user_id', 'start_time'])
    op.create_index('ix_bookings_status_start', 'bookings', ['status', 'start_time'])
    # One live booking per slot; closed rows excluded.
    op.create_index(
        'ux_bookings_active_slot',
        'bookings',
        ['slot_id'],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('cancelled', 'rejected')"),
    )

    # Mutually referential slot/booking constraints
    op.create_foreign_key(
        'fk_availability_slots_booking_id',
        'availability_slots',
        'bookings',
        ['booking_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_bookings_slot_id',
        'bookings',
        'availability_slots',
        ['slot_id'],
        ['id'],
        ondelete='RESTRICT',
    )

    # Booking audit events
    op.create_table(
        'booking_events',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('from_status', sa.String(length=32), nullable=True),
        sa.Column('to_status', sa.String(length=32), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_booking_events_booking_id', 'booking_events', ['booking_id'])
    op.create_index('ix_booking_events_actor_id', 'booking_events', ['actor_id'])
    op.create_index('ix_booking_events_booking_created', 'booking_events', ['booking_id', 'created_at'])

    # Expert session notes
    op.create_table(
        'session_notes',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('visibility', sa.Enum('private', 'shared', name='booking_note_visibility', native_enum=False, create_type=False), server_default='private', nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_session_notes_booking_id', 'session_notes', ['booking_id'])
    op.create_index('ix_session_notes_author_id', 'session_notes', ['author_id'])
    op.create_index('ix_session_notes_booking_created', 'session_notes', ['booking_id', 'created_at'])

    # Seeker feedback
    op.create_table(
        'session_feedbacks',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expert_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('expert_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=False),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id', name='uq_session_feedback_booking'),
    )
    op.create_index('ix_session_feedbacks_booking_id', 'session_feedbacks', ['booking_id'], unique=True)
    op.create_index('ix_session_feedbacks_user_id', 'session_feedbacks', ['user_id'])
    op.create_index('ix_session_feedbacks_expert_id', 'session_feedbacks', ['expert_id'])
    op.create_index('ix_session_feedbacks_expert', 'session_feedbacks', ['expert_id', 'created_at'])

    # Per-expert Google Calendar connections
    op.create_table(
        'expert_calendar_connections',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('expert_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('expert_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('google_email', sa.String(length=320), nullable=True),
        sa.Column('google_account_id', sa.String(length=64), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('access_token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calendar_id', sa.String(length=255), server_default='primary', nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('expert_id', name='uq_expert_calendar_connection'),
    )
    op.create_index('ix_expert_calendar_connections_expert_id', 'expert_calendar_connections', ['expert_id'], unique=True)


def downgrade() -> None:
    op.drop_constraint('fk_bookings_slot_id', 'bookings', type_='foreignkey')
    op.drop_constraint('fk_availability_slots_booking_id', 'availability_slots', type_='foreignkey')

    op.drop_index('ix_expert_calendar_connections_expert_id', table_name='expert_calendar_connections')
    op.drop_table('expert_calendar_connections')

    op.drop_index('ix_session_feedbacks_expert', table_name='session_feedbacks')
    op.drop_index('ix_session_feedbacks_expert_id', table_name='session_feedbacks')
    op.drop_index('ix_session_feedbacks_user_id', table_name='session_feedbacks')
    op.drop_index('ix_session_feedbacks_booking_id', table_name='session_feedbacks')
    op.drop_table('session_feedbacks')

    op.drop_index('ix_session_notes_booking_created', table_name='session_notes')
    op.drop_index('ix_session_notes_author_id', table_name='session_notes')
    op.drop_index('ix_session_notes_booking_id', table_name='session_notes')
    op.drop_table('session_notes')

    op.drop_index('ix_booking_events_booking_created', table_name='booking_events')
    op.drop_index('ix_booking_events_actor_id', table_name='booking_events')
    op.drop_index('ix_booking_events_booking_id', table_name='booking_events')
    op.drop_table('booking_events')

    op.drop_index('ux_bookings_active_slot', table_name='bookings')
    op.drop_index('ix_bookings_status_start', table_name='bookings')
    op.drop_index('ix_bookings_user_start', table_name='bookings')
    op.drop_index('ix_bookings_expert_start', table_name='bookings')
    op.drop_index('ix_bookings_start_time', table_name='bookings')
    op.drop_index('ix_bookings_cancelled_by_id', table_name='bookings')
    op.drop_index('ix_bookings_user_id', table_name='bookings')
    op.drop_index('ix_bookings_expert_id', table_name='bookings')
    op.drop_index('ix_bookings_slot_id', table_name='bookings')
    op.drop_table('bookings')

    op.drop_index('ix_availability_slots_status', table_name='availability_slots')
    op.drop_index('ix_availability_slots_expert_start', table_name='availability_slots')
    op.drop_index('ix_availability_slots_start_time', table_name='availability_slots')
    op.drop_index('ix_availability_slots_booking_id', table_name='availability_slots')
    op.drop_index('ix_availability_slots_rule_id', table_name='availability_slots')
    op.drop_index('ix_availability_slots_expert_id', table_name='availability_slots')
    op.drop_table('availability_slots')

    op.drop_index('ix_availability_rules_expert', table_name='availability_rules')
    op.drop_index('ix_availability_rules_expert_id', table_name='availability_rules')
    op.drop_table('availability_rules')

    op.drop_index('ix_expert_profiles_accepting', table_name='expert_profiles')
    op.drop_index('ix_expert_profiles_user_id', table_name='expert_profiles')
    op.drop_table('expert_profiles')

    op.execute("DROP TYPE IF EXISTS booking_note_visibility")
    op.execute("DROP TYPE IF EXISTS booking_calendar_sync_status")
    op.execute("DROP TYPE IF EXISTS booking_slot_status")
    op.execute("DROP TYPE IF EXISTS booking_status")

    # NOTE: Booking enum values stay; removal is unsupported.
