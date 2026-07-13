"""add_command_center_models

Revision ID: 7c0d1e413ef3
Revises: 6f0b1d413ef2
Create Date: 2026-07-12 21:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7c0d1e413ef3'
down_revision: Union[str, None] = '6f0b1d413ef2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. commands table
    op.create_table(
        'commands',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('command_type', sa.String(length=255), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_commands_id'), 'commands', ['id'], unique=False)

    # 2. command_approvals table
    op.create_table(
        'command_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('command_id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['command_id'], ['commands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_command_approvals_id'), 'command_approvals', ['id'], unique=False)

    # 3. command_executions table
    op.create_table(
        'command_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('command_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['command_id'], ['commands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_command_executions_id'), 'command_executions', ['id'], unique=False)

    # 4. command_audits table
    op.create_table(
        'command_audits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('command_id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('previous_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['command_id'], ['commands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_command_audits_id'), 'command_audits', ['id'], unique=False)

    # 5. command_results table
    op.create_table(
        'command_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('command_id', sa.Integer(), nullable=False),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['command_id'], ['commands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_command_results_id'), 'command_results', ['id'], unique=False)

    # 6. command_comments table
    op.create_table(
        'command_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('command_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['command_id'], ['commands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_command_comments_id'), 'command_comments', ['id'], unique=False)

    # 7. command_attachments table
    op.create_table(
        'command_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('command_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['command_id'], ['commands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_command_attachments_id'), 'command_attachments', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('command_attachments')
    op.drop_table('command_comments')
    op.drop_table('command_results')
    op.drop_table('command_audits')
    op.drop_table('command_executions')
    op.drop_table('command_approvals')
    op.drop_table('commands')
