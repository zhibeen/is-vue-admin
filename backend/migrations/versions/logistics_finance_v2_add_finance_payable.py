"""Add logistics statement v2 and finance payable models

Revision ID: logistics_finance_v2
Revises: add_logistics_statement
Create Date: 2025-12-20 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'logistics_finance_v2'
down_revision = 'add_logistics_statement'
branch_labels = None
depends_on = None


def upgrade():
    # ========== 创建财务付款池表 ========== #
    op.create_table('fin_payment_pools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_no', sa.String(length=50), nullable=False, comment='付款池编号'),
        sa.Column('pool_name', sa.String(length=200), nullable=False, comment='付款池名称'),
        sa.Column('scheduled_date', sa.Date(), nullable=False, comment='计划付款日期'),
        sa.Column('total_amount', sa.DECIMAL(precision=18, scale=2), server_default='0', nullable=False, comment='总金额'),
        sa.Column('total_count', sa.Integer(), server_default='0', nullable=False, comment='应付单数量'),
        sa.Column('status', sa.String(length=20), server_default='draft', nullable=False, comment='状态'),
        sa.Column('approved_by_id', sa.Integer(), nullable=True, comment='审批人'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='审批时间'),
        sa.Column('executed_by_id', sa.Integer(), nullable=True, comment='执行人（出纳）'),
        sa.Column('executed_at', sa.DateTime(), nullable=True, comment='执行时间'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['executed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pool_no')
    )
    
    # ========== 创建财务应付单表 ========== #
    op.create_table('fin_payables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payable_no', sa.String(length=50), nullable=False, comment='应付单号'),
        sa.Column('source_type', sa.String(length=20), nullable=False, comment='来源类型（supply_contract/logistics/expense）'),
        sa.Column('source_id', sa.Integer(), nullable=False, comment='来源单据ID'),
        sa.Column('source_no', sa.String(length=50), nullable=True, comment='来源单号'),
        sa.Column('payee_type', sa.String(length=20), nullable=False, comment='收款方类型（supplier/logistics_provider/employee）'),
        sa.Column('payee_id', sa.Integer(), nullable=False, comment='收款方ID'),
        sa.Column('payee_name', sa.String(length=200), nullable=False, comment='收款方名称'),
        sa.Column('bank_name', sa.String(length=100), nullable=True, comment='开户银行'),
        sa.Column('bank_account', sa.String(length=50), nullable=True, comment='银行账号'),
        sa.Column('bank_account_name', sa.String(length=100), nullable=True, comment='账户名称'),
        sa.Column('payable_amount', sa.DECIMAL(precision=18, scale=2), nullable=False, comment='应付金额'),
        sa.Column('paid_amount', sa.DECIMAL(precision=18, scale=2), server_default='0', nullable=False, comment='已付金额'),
        sa.Column('currency', sa.String(length=10), server_default='CNY', nullable=False, comment='币种'),
        sa.Column('due_date', sa.Date(), nullable=True, comment='应付日期'),
        sa.Column('priority', sa.Integer(), server_default='3', nullable=False, comment='优先级(1-最高, 5-最低)'),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False, comment='状态'),
        sa.Column('approved_by_id', sa.Integer(), nullable=True, comment='审批人'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='审批时间'),
        sa.Column('rejection_reason', sa.Text(), nullable=True, comment='驳回原因'),
        sa.Column('payment_pool_id', sa.Integer(), nullable=True, comment='付款池ID'),
        sa.Column('paid_at', sa.DateTime(), nullable=True, comment='付款时间'),
        sa.Column('payment_voucher_id', sa.Integer(), nullable=True, comment='付款凭证ID'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['payment_pool_id'], ['fin_payment_pools.id'], ),
        sa.ForeignKeyConstraint(['payment_voucher_id'], ['document_center.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payable_no')
    )
    
    # ========== 创建对账单-物流服务关联表 ========== #
    op.create_table('statement_service_relations',
        sa.Column('statement_id', sa.Integer(), nullable=False),
        sa.Column('logistics_service_id', sa.Integer(), nullable=False),
        sa.Column('reconciled_amount', sa.DECIMAL(precision=18, scale=2), nullable=False, comment='本次对账金额'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['logistics_service_id'], ['shipment_logistics_services.id'], ),
        sa.ForeignKeyConstraint(['statement_id'], ['logistics_statements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('statement_id', 'logistics_service_id')
    )
    
    # ========== 修改 logistics_statements 表（添加新字段，保留旧字段）========== #
    op.add_column('logistics_statements', sa.Column('statement_period_start', sa.Date(), nullable=True, comment='对账周期-开始'))
    op.add_column('logistics_statements', sa.Column('statement_period_end', sa.Date(), nullable=True, comment='对账周期-结束'))
    op.add_column('logistics_statements', sa.Column('finance_payable_id', sa.Integer(), nullable=True, comment='关联财务应付单ID（SERC）'))
    op.add_column('logistics_statements', sa.Column('submitted_to_finance_at', sa.DateTime(), nullable=True, comment='提交财务时间'))
    op.add_column('logistics_statements', sa.Column('attachment_ids', postgresql.ARRAY(sa.Integer()), nullable=True, comment='对账单附件ID列表（凭证中心）'))
    op.add_column('logistics_statements', sa.Column('created_by_id', sa.Integer(), nullable=True, comment='创建人ID'))
    
    # 更新 status 字段的注释（扩展状态）
    # PostgreSQL: ALTER TABLE ... ALTER COLUMN ... SET DEFAULT 会保留现有数据
    
    # 标记旧字段为 DEPRECATED（通过 COMMENT）
    op.execute("COMMENT ON COLUMN logistics_statements.shipment_id IS '[DEPRECATED] 发货单ID，新版本使用多对多关联'")
    op.execute("COMMENT ON COLUMN logistics_statements.statement_date IS '[DEPRECATED] 对账日期，使用 statement_period_end'")
    op.execute("COMMENT ON COLUMN logistics_statements.payment_method IS '[DEPRECATED] 付款方式，由财务模块管理'")
    
    # 更新现有数据：将 statement_date 复制到 statement_period_end
    op.execute("""
        UPDATE logistics_statements 
        SET statement_period_start = statement_date - INTERVAL '30 days',
            statement_period_end = statement_date
        WHERE statement_date IS NOT NULL
    """)


def downgrade():
    # ========== 回滚 logistics_statements 表修改 ========== #
    op.drop_column('logistics_statements', 'created_by_id')
    op.drop_column('logistics_statements', 'attachment_ids')
    op.drop_column('logistics_statements', 'submitted_to_finance_at')
    op.drop_column('logistics_statements', 'finance_payable_id')
    op.drop_column('logistics_statements', 'statement_period_end')
    op.drop_column('logistics_statements', 'statement_period_start')
    
    # ========== 删除关联表 ========== #
    op.drop_table('statement_service_relations')
    
    # ========== 删除财务表 ========== #
    op.drop_table('fin_payables')
    op.drop_table('fin_payment_pools')

