"""Add notification tables and preference fields."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_notifications'
down_revision = '0005_consultation_messages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add notification preference fields to profiles
    op.add_column('profiles', sa.Column('notify_insights', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('profiles', sa.Column('notify_growth', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('profiles', sa.Column('notify_announcements', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('profiles', sa.Column('notify_email', sa.Boolean(), nullable=False, server_default='true'))

    # Create notification enum first
    op.execute("CREATE TYPE notification_type AS ENUM ('daily_guidance', 'reading_reminder', 'insight_update', 'growth_alert', 'platform_announcement', 'reading_completed')")
    op.execute("CREATE TYPE notification_priority AS ENUM ('low', 'normal', 'high')")
    op.execute("CREATE TYPE notification_channel AS ENUM ('in_app', 'email')")
    op.execute("CREATE TYPE delivery_status AS ENUM ('pending', 'sent', 'delivered', 'failed')")

    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Enum('daily_guidance', 'reading_reminder', 'insight_update', 'growth_alert', 'platform_announcement', 'reading_completed', name='notification_type', native_enum=False, create_type=False), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', name='notification_priority', native_enum=False, create_type=False), server_default='normal', nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_created', 'notifications', ['user_id', 'created_at'])
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'])
    op.create_index('ix_notifications_idempotency_key', 'notifications', ['idempotency_key'], unique=True)

    # Create notification_deliveries table
    op.create_table('notification_deliveries',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('notification_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('notifications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.Enum('in_app', 'email', name='notification_channel', native_enum=False, create_type=False), nullable=False),
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'failed', name='delivery_status', native_enum=False, create_type=False), server_default='pending', nullable=False),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_deliveries_notification', 'notification_deliveries', ['notification_id'])


def downgrade() -> None:
    op.drop_index('ix_notification_deliveries_notification', table_name='notification_deliveries')
    op.drop_table('notification_deliveries')
    op.drop_index('ix_notifications_idempotency_key', table_name='notifications')
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_notifications_user_created', table_name='notifications')
    op.drop_table('notifications')

    op.execute("DROP TYPE IF EXISTS delivery_status")
    op.execute("DROP TYPE IF EXISTS notification_channel")
    op.execute("DROP TYPE IF EXISTS notification_priority")
    op.execute("DROP TYPE IF EXISTS notification_type")

    op.drop_column('profiles', 'notify_email')
    op.drop_column('profiles', 'notify_announcements')
    op.drop_column('profiles', 'notify_growth')
    op.drop_column('profiles', 'notify_insights')
