"""Add phone_numbers table.

Revision ID: 002
Revises: 001
Create Date: 2026-03-03 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Create phone_numbers table."""
    op.create_table(
        'phone_numbers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('twilio_phone_sid', sa.String(100), nullable=False),
        sa.Column('friendly_name', sa.String(100), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=False, server_default='US'),
        sa.Column('area_code', sa.String(10), nullable=True),
        sa.Column('locality', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('monthly_cost', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('inbound_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('outbound_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('webhook_configured_at', sa.String(50), nullable=True),
        sa.Column('provisioned_at', sa.String(50), nullable=True),
        sa.Column('released_at', sa.String(50), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('call_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_call_at', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number'),
        sa.UniqueConstraint('twilio_phone_sid'),
    )
    op.create_index(op.f('ix_phone_numbers_agent_id'), 'phone_numbers', ['agent_id'], unique=False)
    op.create_index(op.f('ix_phone_numbers_company_id'), 'phone_numbers', ['company_id'], unique=False)


def downgrade():
    """Drop phone_numbers table."""
    op.drop_index(op.f('ix_phone_numbers_company_id'), table_name='phone_numbers')
    op.drop_index(op.f('ix_phone_numbers_agent_id'), table_name='phone_numbers')
    op.drop_table('phone_numbers')
