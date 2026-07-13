"""Add database indexes for incident management performance

Revision ID: 2026_07_11_1400_add_incident_indexes
Revises: 2b3c4d5e6f7a_phase3
Create Date: 2026-07-11 14:00:00.000000

Add composite indexes for frequently filtered and searched columns
to improve query performance on incident listing and statistics.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2026_07_11_1400_add_incident_indexes'
down_revision: Union[str, None] = '7e5a3beab023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for most common filter pattern: active incidents by status/priority
    op.create_index(
        'idx_incidents_status_priority',
        'incidents',
        ['is_deleted', 'status', 'priority'],
        unique=False
    )
    
    # Composite index for severity-based queries with recency
    op.create_index(
        'idx_incidents_severity_created',
        'incidents',
        ['is_deleted', 'severity', 'created_at'],
        unique=False
    )
    
    # Composite index for category filtering
    op.create_index(
        'idx_incidents_category_status',
        'incidents',
        ['is_deleted', 'category', 'status'],
        unique=False
    )
    
    # Trigram index for full-text search on title and description
    if op.get_bind().dialect.name == 'postgresql':
        op.execute(
            'CREATE INDEX idx_incidents_search ON incidents USING GIN (title gin_trgm_ops || description gin_trgm_ops)'
        )
    
    # Index for SLA breach detection
    op.create_index(
        'idx_incidents_sla_expires',
        'incidents',
        ['is_deleted', 'sla_expires_at'],
        unique=False,
        postgresql_where=sa.text('sla_expires_at IS NOT NULL')
    )
    
    # Index for timeline lookups
    op.create_index(
        'idx_incident_timeline_incident_created',
        'incident_timeline',
        ['incident_id', 'created_at'],
        unique=False
    )
    
    # Index for comment lookups
    op.create_index(
        'idx_incident_comments_incident_created',
        'incident_comments',
        ['incident_id', 'created_at'],
        unique=False
    )
    
    # Add unique constraint to M2M association table to prevent duplicates
    if op.get_bind().dialect.name != 'sqlite':
        op.create_unique_constraint(
            'uq_incident_user_assignment',
            'incident_assignments_association',
            ['incident_id', 'user_id']
        )


def downgrade() -> None:
    # Drop unique constraint first
    if op.get_bind().dialect.name != 'sqlite':
        op.drop_constraint('uq_incident_user_assignment', 'incident_assignments_association', type_='unique')
    
    # Drop indexes in reverse order
    op.drop_index('idx_incident_comments_incident_created', table_name='incident_comments')
    op.drop_index('idx_incident_timeline_incident_created', table_name='incident_timeline')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP INDEX idx_incidents_search')
    op.drop_index('idx_incidents_sla_expires', table_name='incidents')
    op.drop_index('idx_incidents_category_status', table_name='incidents')
    op.drop_index('idx_incidents_severity_created', table_name='incidents')
    op.drop_index('idx_incidents_status_priority', table_name='incidents')