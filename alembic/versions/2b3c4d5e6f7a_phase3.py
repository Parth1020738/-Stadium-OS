# Alembic script template for Phase 3 User Service
"""Phase 3 migrations

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-07-10 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2b3c4d5e6f7a'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new columns to users
    op.add_column('users', sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('version_id', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('users', sa.Column('status', sa.String(), nullable=True, server_default='Pending'))

    # Create new tables
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('details', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)

    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)

    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)

    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)

    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(), nullable=True, server_default='en'),
        sa.Column('receive_notifications', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_preferences_id'), 'user_preferences', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('user_preferences')
    op.drop_table('user_profiles')
    op.drop_table('teams')
    op.drop_table('departments')
    op.drop_table('organizations')
    op.drop_column('users', 'status')
    op.drop_column('users', 'version_id')
    op.drop_column('users', 'is_deleted')
