"""Add analytics indexes for performance.

Revision ID: 003
Revises: 002
Create Date: 2026-03-04 03:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Create analytics indexes."""
    # Index on created_at for date filtering
    op.create_index(
        'ix_call_created_at',
        'calls',
        ['created_at'],
        unique=False,
    )

    # Index on status for status grouping
    op.create_index(
        'ix_call_status',
        'calls',
        ['status'],
        unique=False,
    )

    # Composite index on agent_id + created_at
    op.create_index(
        'ix_call_agent_id_created_at',
        'calls',
        ['agent_id', 'created_at'],
        unique=False,
    )

    # Index on duration for sorting/filtering
    op.create_index(
        'ix_call_duration_seconds',
        'calls',
        ['duration_seconds'],
        unique=False,
    )

    # Index on cost for cost queries
    op.create_index(
        'ix_call_ai_cost_usd',
        'calls',
        ['ai_cost_usd'],
        unique=False,
    )

    # Index on company_id for company-level queries
    op.create_index(
        'ix_call_company_id_created_at',
        'calls',
        ['company_id', 'created_at'],
        unique=False,
    )

    # Index on to_number for phone-based queries
    op.create_index(
        'ix_call_to_number',
        'calls',
        ['to_number'],
        unique=False,
    )


def downgrade():
    """Drop analytics indexes."""
    op.drop_index('ix_call_to_number', table_name='calls')
    op.drop_index('ix_call_company_id_created_at', table_name='calls')
    op.drop_index('ix_call_ai_cost_usd', table_name='calls')
    op.drop_index('ix_call_duration_seconds', table_name='calls')
    op.drop_index('ix_call_agent_id_created_at', table_name='calls')
    op.drop_index('ix_call_status', table_name='calls')
    op.drop_index('ix_call_created_at', table_name='calls')
