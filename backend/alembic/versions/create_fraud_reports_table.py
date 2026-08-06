"""create fraud_reports table

Revision ID: create_fraud_reports_table
Revises: 
Create Date: 2026-08-06 10:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = 'create_fraud_reports_table'
down_revision = "e42b4ce93dd2"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'fraud_reports',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('total_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('blocked_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('blocked_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('top_triggered_rules', pg.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

def downgrade():
    op.drop_table('fraud_reports')