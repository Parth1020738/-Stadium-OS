"""add_indexes_and_locking

Revision ID: 578a6f3b2d1c
Revises: 46749e37d8f7
Create Date: 2026-07-12 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '578a6f3b2d1c'
down_revision: Union[str, None] = '46749e37d8f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update transit_route_stops M2M table with is_deleted and version_id
    op.add_column('transit_route_stops', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('transit_route_stops', sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'))

    # 2. Drop version_id from transit_telemetry
    op.drop_column('transit_telemetry', 'version_id')

    # 3. Create TransitAlert table
    op.create_table('transit_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_code', sa.String(length=100), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=True),
        sa.Column('hub_id', sa.String(length=100), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('delay_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('estimated_resolution_time', sa.DateTime(), nullable=True),
        sa.Column('reported_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['route_id'], ['transit_routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transit_alerts_alert_code'), 'transit_alerts', ['alert_code'], unique=True)
    op.create_index(op.f('ix_transit_alerts_id'), 'transit_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_transit_alerts_route_id'), 'transit_alerts', ['route_id'], unique=False)
    op.create_index(op.f('ix_transit_alerts_hub_id'), 'transit_alerts', ['hub_id'], unique=False)

    # 4. Create composite indexes
    op.create_index('ix_transit_telemetry_vehicle_timestamp', 'transit_telemetry', ['vehicle_id', 'timestamp'], unique=False)
    op.create_index('ix_transit_etas_trip_stop', 'transit_etas', ['trip_id', 'stop_id'], unique=False)
    op.create_index('ix_transit_occupancies_vehicle_stop', 'transit_occupancies', ['vehicle_id', 'stop_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_transit_occupancies_vehicle_stop', table_name='transit_occupancies')
    op.drop_index('ix_transit_etas_trip_stop', table_name='transit_etas')
    op.drop_index('ix_transit_telemetry_vehicle_timestamp', table_name='transit_telemetry')

    op.drop_index(op.f('ix_transit_alerts_hub_id'), table_name='transit_alerts')
    op.drop_index(op.f('ix_transit_alerts_route_id'), table_name='transit_alerts')
    op.drop_index(op.f('ix_transit_alerts_id'), table_name='transit_alerts')
    op.drop_index(op.f('ix_transit_alerts_alert_code'), table_name='transit_alerts')
    op.drop_table('transit_alerts')

    op.add_column('transit_telemetry', sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'))
    op.drop_column('transit_route_stops', 'version_id')
    op.drop_column('transit_route_stops', 'is_deleted')
