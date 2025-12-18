"""add_customs_indexes_and_audit_table

Revision ID: 17e4792b2e4d
Revises: 884c75613301
Create Date: 2025-12-17 13:17:14.677812

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17e4792b2e4d'
down_revision = '884c75613301'
branch_labels = None
depends_on = None


def upgrade():
    """
    添加报关单性能优化索引和审计日志表
    """
    # 1. 创建审计日志表（如果不存在）
    op.execute("""
        CREATE TABLE IF NOT EXISTS customs_declaration_audit_logs (
            id SERIAL PRIMARY KEY,
            declaration_id INTEGER NOT NULL REFERENCES customs_declarations(id) ON DELETE CASCADE,
            action VARCHAR(50) NOT NULL,
            action_description VARCHAR(255) NOT NULL,
            old_value JSONB,
            new_value JSONB,
            changes_summary TEXT,
            operator_id INTEGER,
            operator_name VARCHAR(100),
            ip_address VARCHAR(50),
            user_agent VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 2. 为审计日志表添加索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_declaration ON customs_declaration_audit_logs(declaration_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON customs_declaration_audit_logs(action);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_operator ON customs_declaration_audit_logs(operator_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_created_at ON customs_declaration_audit_logs(created_at DESC);")
    
    # 3. 为报关单主表添加性能优化索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_status ON customs_declarations(status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_company ON customs_declarations(internal_shipper_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_export_date ON customs_declarations(export_date DESC);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_created_at ON customs_declarations(created_at DESC);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_entry_no ON customs_declarations(entry_no);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_pre_entry_no ON customs_declarations(pre_entry_no);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_customs_no ON customs_declarations(customs_no);")
    
    # 4. 复合索引（常用查询组合）
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_status_company ON customs_declarations(status, internal_shipper_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_declarations_status_date ON customs_declarations(status, export_date DESC);")
    
    # 5. 为报关单明细表添加索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_decl_items_declaration ON customs_declaration_items(declaration_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_decl_items_product ON customs_declaration_items(product_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_decl_items_supplier ON customs_declaration_items(supplier_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_decl_items_hs_code ON customs_declaration_items(hs_code);")


def downgrade():
    """
    回滚索引和审计日志表
    """
    # 1. 删除审计日志表索引
    op.execute("DROP INDEX IF EXISTS idx_audit_declaration;")
    op.execute("DROP INDEX IF EXISTS idx_audit_action;")
    op.execute("DROP INDEX IF EXISTS idx_audit_operator;")
    op.execute("DROP INDEX IF EXISTS idx_audit_created_at;")
    
    # 2. 删除审计日志表
    op.execute("DROP TABLE IF EXISTS customs_declaration_audit_logs;")
    
    # 3. 删除报关单索引
    op.execute("DROP INDEX IF EXISTS idx_declarations_status;")
    op.execute("DROP INDEX IF EXISTS idx_declarations_company;")
    op.execute("DROP INDEX IF EXISTS idx_declarations_export_date;")
    op.execute("DROP INDEX IF EXISTS idx_declarations_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_declarations_entry_no;")
    op.execute("DROP INDEX IF EXISTS idx_declarations_pre_entry_no;")
    op.execute("DROP INDEX IF EXISTS idx_declarations_customs_no;")
    op.execute("DROP INDEX IF EXISTS idx_declarations_status_company;")
    op.execute("DROP INDEX IF EXISTS idx_declarations_status_date;")
    
    # 4. 删除明细表索引
    op.execute("DROP INDEX IF EXISTS idx_decl_items_declaration;")
    op.execute("DROP INDEX IF EXISTS idx_decl_items_product;")
    op.execute("DROP INDEX IF EXISTS idx_decl_items_supplier;")
    op.execute("DROP INDEX IF EXISTS idx_decl_items_hs_code;")
