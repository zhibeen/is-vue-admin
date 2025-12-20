"""添加物流对账单和付款单表

Revision ID: add_logistics_statement
Revises: 9ff3fc388de3
Create Date: 2025-12-19 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_logistics_statement'
down_revision = '91c4ca475d77'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建 logistics_statements 表
    op.create_table(
        'logistics_statements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('statement_no', sa.String(length=50), nullable=False, comment='对账单号'),
        sa.Column('shipment_id', sa.Integer(), nullable=False, comment='发货单ID'),
        sa.Column('logistics_provider_id', sa.Integer(), nullable=False, comment='物流服务商ID'),
        sa.Column('statement_date', sa.Date(), comment='对账日期'),
        sa.Column('total_amount', sa.DECIMAL(18, 2), comment='总金额'),
        sa.Column('currency', sa.String(length=10), server_default='CNY', comment='币种'),
        sa.Column('payment_method', sa.String(length=20), comment='付款方式'),
        sa.Column('status', sa.String(length=20), server_default='draft', comment='状态'),
        sa.Column('confirmed_by_id', sa.Integer(), comment='确认人ID'),
        sa.Column('confirmed_at', sa.DateTime(), comment='确认时间'),
        sa.Column('notes', sa.Text(), comment='备注'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('statement_no', name='uq_logistics_statements_no'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipment_orders.id']),
        sa.ForeignKeyConstraint(['logistics_provider_id'], ['logistics_providers.id']),
        sa.ForeignKeyConstraint(['confirmed_by_id'], ['users.id']),
    )
    
    # 2. 创建 logistics_payments 表
    op.create_table(
        'logistics_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_no', sa.String(length=50), nullable=False, comment='付款单号'),
        sa.Column('statement_id', sa.Integer(), nullable=False, comment='对账单ID'),
        sa.Column('payment_date', sa.Date(), comment='付款日期'),
        sa.Column('payment_amount', sa.DECIMAL(18, 2), comment='付款金额'),
        sa.Column('currency', sa.String(length=10), server_default='CNY', comment='币种'),
        sa.Column('payment_pool_id', sa.Integer(), comment='付款池ID'),
        sa.Column('status', sa.String(length=20), server_default='pending', comment='状态'),
        sa.Column('approved_by_id', sa.Integer(), comment='审批人ID'),
        sa.Column('approved_at', sa.DateTime(), comment='审批时间'),
        sa.Column('paid_at', sa.DateTime(), comment='付款时间'),
        sa.Column('notes', sa.Text(), comment='备注'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_no', name='uq_logistics_payments_no'),
        sa.ForeignKeyConstraint(['statement_id'], ['logistics_statements.id']),
        sa.ForeignKeyConstraint(['payment_pool_id'], ['fin_payment_pool.id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id']),
    )
    
    # 创建索引
    op.create_index('idx_ls_shipment_id', 'logistics_statements', ['shipment_id'])
    op.create_index('idx_ls_provider_id', 'logistics_statements', ['logistics_provider_id'])
    op.create_index('idx_ls_status', 'logistics_statements', ['status'])
    op.create_index('idx_lp_statement_id', 'logistics_payments', ['statement_id'])
    op.create_index('idx_lp_status', 'logistics_payments', ['status'])


def downgrade():
    # 删除索引
    op.drop_index('idx_lp_status', table_name='logistics_payments')
    op.drop_index('idx_lp_statement_id', table_name='logistics_payments')
    op.drop_index('idx_ls_status', table_name='logistics_statements')
    op.drop_index('idx_ls_provider_id', table_name='logistics_statements')
    op.drop_index('idx_ls_shipment_id', table_name='logistics_statements')
    
    # 删除表
    op.drop_table('logistics_payments')
    op.drop_table('logistics_statements')

