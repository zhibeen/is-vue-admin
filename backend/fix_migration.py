#!/usr/bin/env python3
"""
修复三方服务表迁移脚本
由于原来的迁移文件尝试创建新表时约束名冲突，需要手动修复
"""

import os
import sys
from datetime import datetime

# 生成迁移文件名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
migration_file = f"backend/migrations/versions/{timestamp}_fix_third_party_tables.py"

migration_content = '''"""fix third party tables

Revision ID: {timestamp}
Revises: 43c1ea6841c3
Create Date: {create_date}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '{timestamp}'
down_revision = '43c1ea6841c3'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 重命名 third_party_services 表
    op.rename_table('third_party_services', 'warehouse_third_party_services')
    
    # 2. 重命名 third_party_warehouses 表
    op.rename_table('third_party_warehouses', 'warehouse_third_party_warehouses')
    
    # 3. 重命名 third_party_warehouse_maps 表
    op.rename_table('third_party_warehouse_maps', 'warehouse_third_party_warehouse_maps')
    
    # 4. 重命名 third_party_sku_mappings 表
    op.rename_table('third_party_sku_mappings', 'warehouse_third_party_sku_mappings')
    
    # 5. 更新外键约束名（如果需要）
    # 注意：PostgreSQL 中外键约束名是自动生成的，通常不需要手动更新
    # 但如果有自定义的约束名，需要在这里更新


def downgrade():
    # 回滚操作
    op.rename_table('warehouse_third_party_services', 'third_party_services')
    op.rename_table('warehouse_third_party_warehouses', 'third_party_warehouses')
    op.rename_table('warehouse_third_party_warehouse_maps', 'third_party_warehouse_maps')
    op.rename_table('warehouse_third_party_sku_mappings', 'third_party_sku_mappings')
'''.format(
    timestamp=timestamp,
    create_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
)

# 写入迁移文件
os.makedirs(os.path.dirname(migration_file), exist_ok=True)
with open(migration_file, 'w', encoding='utf-8') as f:
    f.write(migration_content)

print(f"已创建迁移文件: {migration_file}")
print("请运行: docker compose exec backend flask db upgrade")
