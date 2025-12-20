"""创建物流服务商和凭证管理中心表

Revision ID: 20251219_logistics_doc
Revises: fea4aae536ba
Create Date: 2025-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251219_logistics_doc'
down_revision = 'd7504d53bb1f'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建 logistics_providers 表（物流服务商）
    op.create_table(
        'logistics_providers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False, comment='服务商名称'),
        sa.Column('provider_code', sa.String(length=50), nullable=False, comment='服务商编码'),
        sa.Column('service_type', sa.String(length=50), nullable=True, comment='服务类型'),
        sa.Column('payment_method', sa.String(length=20), nullable=True, comment='付款方式'),
        sa.Column('settlement_cycle', sa.String(length=20), nullable=True, comment='结算周期'),
        sa.Column('contact_name', sa.String(length=50), nullable=True, comment='联系人'),
        sa.Column('contact_phone', sa.String(length=30), nullable=True, comment='联系电话'),
        sa.Column('contact_email', sa.String(length=100), nullable=True, comment='邮箱'),
        sa.Column('bank_name', sa.String(length=100), nullable=True, comment='开户银行'),
        sa.Column('bank_account', sa.String(length=50), nullable=True, comment='银行账号'),
        sa.Column('bank_account_name', sa.String(length=100), nullable=True, comment='账户名称'),
        sa.Column('service_areas', postgresql.ARRAY(sa.String()), nullable=True, comment='服务区域'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='启用状态'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_code', name='uq_logistics_providers_code')
    )
    
    # 创建索引
    op.create_index('idx_lp_provider_name', 'logistics_providers', ['provider_name'])
    op.create_index('idx_lp_is_active', 'logistics_providers', ['is_active'])
    
    # 2. 创建 document_center 表（凭证管理中心）
    op.create_table(
        'document_center',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_type', sa.String(length=30), nullable=False, comment='业务类型'),
        sa.Column('document_type', sa.String(length=50), nullable=True, comment='凭证类型'),
        sa.Column('document_category', sa.String(length=30), nullable=True, comment='文档分类'),
        sa.Column('business_id', sa.Integer(), nullable=False, comment='业务单据ID'),
        sa.Column('business_no', sa.String(length=100), nullable=True, comment='业务单据编号'),
        sa.Column('file_name', sa.String(length=255), nullable=False, comment='文件名'),
        sa.Column('file_path', sa.String(length=500), nullable=False, comment='文件路径'),
        sa.Column('file_size', sa.BigInteger(), nullable=True, comment='文件大小(bytes)'),
        sa.Column('file_type', sa.String(length=20), nullable=True, comment='文件扩展名'),
        sa.Column('file_url', sa.String(length=500), nullable=True, comment='可访问URL'),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False, comment='上传人ID'),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, comment='上传时间'),
        sa.Column('audit_status', sa.String(length=20), server_default='pending', nullable=False, comment='审核状态'),
        sa.Column('audited_by_id', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('audited_at', sa.DateTime(), nullable=True, comment='审核时间'),
        sa.Column('audit_notes', sa.Text(), nullable=True, comment='审核备注'),
        sa.Column('archived', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='是否已归档'),
        sa.Column('archive_path', sa.String(length=500), nullable=True, comment='归档路径'),
        sa.Column('archived_at', sa.DateTime(), nullable=True, comment='归档时间'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['audited_by_id'], ['users.id'], )
    )
    
    # 创建索引
    op.create_index('idx_dc_business_type_id', 'document_center', ['business_type', 'business_id'])
    op.create_index('idx_dc_business_no', 'document_center', ['business_no'])
    op.create_index('idx_dc_uploaded_by', 'document_center', ['uploaded_by_id'])
    op.create_index('idx_dc_audit_status', 'document_center', ['audit_status'])
    op.create_index('idx_dc_archived', 'document_center', ['archived'])


def downgrade():
    # 删除索引
    op.drop_index('idx_dc_archived', table_name='document_center')
    op.drop_index('idx_dc_audit_status', table_name='document_center')
    op.drop_index('idx_dc_uploaded_by', table_name='document_center')
    op.drop_index('idx_dc_business_no', table_name='document_center')
    op.drop_index('idx_dc_business_type_id', table_name='document_center')
    
    op.drop_index('idx_lp_is_active', table_name='logistics_providers')
    op.drop_index('idx_lp_provider_name', table_name='logistics_providers')
    
    # 删除表
    op.drop_table('document_center')
    op.drop_table('logistics_providers')

