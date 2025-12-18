"""add_company_codes_for_pre_entry

Revision ID: a1b7855e9a23
Revises: d820af9f5fd7
Create Date: 2025-12-17 12:45:49.936946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b7855e9a23'
down_revision = 'd820af9f5fd7'
branch_labels = None
depends_on = None


def upgrade():
    """
    为现有公司设置公司代码（code字段）
    用于预录入编号生成
    """
    # 注意：code 字段已存在于模型中，此处仅更新数据
    
    # 为现有公司设置代码（根据实际公司名称调整）
    # 格式：公司简码（2-4位字母）
    op.execute("""
        UPDATE sys_companies 
        SET code = CASE 
            WHEN legal_name LIKE '%华瑞%' THEN 'HR'
            WHEN legal_name LIKE '%宁波%' AND legal_name NOT LIKE '%华瑞%' THEN 'NB'
            WHEN legal_name LIKE '%深圳%' THEN 'SZ'
            WHEN legal_name LIKE '%广州%' THEN 'GZ'
            WHEN legal_name LIKE '%上海%' THEN 'SH'
            WHEN legal_name LIKE '%北京%' THEN 'BJ'
            ELSE NULL
        END
        WHERE code IS NULL;
    """)
    
    # 为索引添加注释（如果需要）
    op.execute("""
        COMMENT ON COLUMN sys_companies.code IS '公司代码(用于单据前缀，如：HR-YL-2412-0001)';
    """)


def downgrade():
    """
    回滚：清空公司代码
    """
    op.execute("UPDATE sys_companies SET code = NULL;")
