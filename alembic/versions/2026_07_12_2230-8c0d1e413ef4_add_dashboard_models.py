"""add_dashboard_models

Revision ID: 8c0d1e413ef4
Revises: 7c0d1e413ef3
Create Date: 2026-07-12 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '8c0d1e413ef4'
down_revision: Union[str, None] = '7c0d1e413ef3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. dashboard_widgets
    op.create_table(
        'dashboard_widgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('widget_type', sa.String(length=100), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_widgets_id'), 'dashboard_widgets', ['id'], unique=False)

    # 2. dashboard_layouts
    op.create_table(
        'dashboard_layouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('layout_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_layouts_id'), 'dashboard_layouts', ['id'], unique=False)

    # 3. dashboard_preferences
    op.create_table(
        'dashboard_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(length=50), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_dashboard_preferences_id'), 'dashboard_preferences', ['id'], unique=False)

    # 4. dashboard_snapshots
    op.create_table(
        'dashboard_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_type', sa.String(length=100), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_snapshots_id'), 'dashboard_snapshots', ['id'], unique=False)

    # 5. dashboard_notifications
    op.create_table(
        'dashboard_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False),
        sa.Column('dismissed_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['dismissed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_notifications_id'), 'dashboard_notifications', ['id'], unique=False)

    # 6. dashboard_sessions
    op.create_table(
        'dashboard_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_sessions_id'), 'dashboard_sessions', ['id'], unique=False)

    # 7. dashboard_audits
    op.create_table(
        'dashboard_audits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_audits_id'), 'dashboard_audits', ['id'], unique=False)

    # 8. dashboard_subscriptions
    op.create_table(
        'dashboard_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.String(length=255), nullable=False),
        sa.Column('channel', sa.String(length=100), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_subscriptions_id'), 'dashboard_subscriptions', ['id'], unique=False)

    # 9. dashboard_metrics
    op.create_table(
        'dashboard_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('dimensions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_dashboard_metrics_id'), 'dashboard_metrics', ['id'], unique=False)

    # 10. dashboard_alerts
    op.create_table(
        'dashboard_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_alerts_id'), 'dashboard_alerts', ['id'], unique=False)

    # 11. dashboard_timeline
    op.create_table(
        'dashboard_timeline',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_service', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_timeline_id'), 'dashboard_timeline', ['id'], unique=False)

    # 12. dashboard_cache_metadata
    op.create_table(
        'dashboard_cache_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('ttl_seconds', sa.Integer(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )
    op.create_index(op.f('ix_dashboard_cache_metadata_id'), 'dashboard_cache_metadata', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('dashboard_cache_metadata')
    op.drop_table('dashboard_timeline')
    op.drop_table('dashboard_alerts')
    op.drop_table('dashboard_metrics')
    op.drop_table('dashboard_subscriptions')
    op.drop_table('dashboard_audits')
    op.drop_table('dashboard_sessions')
    op.drop_table('dashboard_notifications')
    op.drop_table('dashboard_snapshots')
    op.drop_table('dashboard_preferences')
    op.drop_table('dashboard_layouts')
    op.drop_table('dashboard_widgets')
