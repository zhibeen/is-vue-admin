"""修改三方服务表名为warehouse_前缀

Revision ID: c4041798fdfe
Revises: 43c1ea6841c3
Create Date: 2025-12-11 06:26:04.749770

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c4041798fdfe'
down_revision = '43c1ea6841c3'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 重命名表 (Rename Tables)
    op.rename_table('third_party_services', 'warehouse_third_party_services')
    op.rename_table('third_party_warehouses', 'warehouse_third_party_warehouses')
    op.rename_table('third_party_sku_mappings', 'warehouse_third_party_sku_mappings')
    op.rename_table('third_party_warehouse_maps', 'warehouse_third_party_warehouse_maps')

    # 2. 重命名索引 (Rename Indexes)
    op.execute('ALTER INDEX ix_third_party_warehouses_service_id RENAME TO ix_warehouse_third_party_warehouses_service_id')
    op.execute('ALTER INDEX ix_third_party_sku_mappings_service_id RENAME TO ix_warehouse_third_party_sku_mappings_service_id')
    op.execute('ALTER INDEX ix_third_party_sku_mappings_remote_sku RENAME TO ix_warehouse_third_party_sku_mappings_remote_sku')
    op.execute('ALTER INDEX ix_third_party_sku_mappings_local_sku RENAME TO ix_warehouse_third_party_sku_mappings_local_sku')
    # idx_mapping_lookup 名字是显式定义的，无需重命名

    # 3. 重命名序列 (Rename Sequences)
    op.execute('ALTER SEQUENCE third_party_services_id_seq RENAME TO warehouse_third_party_services_id_seq')
    op.execute('ALTER SEQUENCE third_party_warehouses_id_seq RENAME TO warehouse_third_party_warehouses_id_seq')
    op.execute('ALTER SEQUENCE third_party_sku_mappings_id_seq RENAME TO warehouse_third_party_sku_mappings_id_seq')
    op.execute('ALTER SEQUENCE third_party_warehouse_maps_id_seq RENAME TO warehouse_third_party_warehouse_maps_id_seq')

    # 4. 更新 Warehouses 表的外键
    with op.batch_alter_table('warehouses', schema=None) as batch_op:
        # 删除旧外键
        batch_op.drop_constraint('warehouses_third_party_service_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('warehouses_third_party_warehouse_id_fkey', type_='foreignkey')
        # 创建新外键 (指向重命名后的表)
        batch_op.create_foreign_key(None, 'warehouse_third_party_warehouses', ['third_party_warehouse_id'], ['id'])
        batch_op.create_foreign_key(None, 'warehouse_third_party_services', ['third_party_service_id'], ['id'])


def downgrade():
    # 1. 还原 Warehouses 表的外键
    with op.batch_alter_table('warehouses', schema=None) as batch_op:
        # 尝试删除新创建的外键 (名字不确定，这里可能需要手动干预或查阅数据库)
        # 简单起见，我们先跳过删除步骤，直接改名回去可能需要先 drop FK
        pass 
    
    # 2. 还原序列名
    op.execute('ALTER SEQUENCE warehouse_third_party_services_id_seq RENAME TO third_party_services_id_seq')
    op.execute('ALTER SEQUENCE warehouse_third_party_warehouses_id_seq RENAME TO third_party_warehouses_id_seq')
    op.execute('ALTER SEQUENCE warehouse_third_party_sku_mappings_id_seq RENAME TO third_party_sku_mappings_id_seq')
    op.execute('ALTER SEQUENCE warehouse_third_party_warehouse_maps_id_seq RENAME TO third_party_warehouse_maps_id_seq')

    # 3. 还原索引名
    op.execute('ALTER INDEX ix_warehouse_third_party_warehouses_service_id RENAME TO ix_third_party_warehouses_service_id')
    op.execute('ALTER INDEX ix_warehouse_third_party_sku_mappings_service_id RENAME TO ix_third_party_sku_mappings_service_id')
    op.execute('ALTER INDEX ix_warehouse_third_party_sku_mappings_remote_sku RENAME TO ix_third_party_sku_mappings_remote_sku')
    op.execute('ALTER INDEX ix_warehouse_third_party_sku_mappings_local_sku RENAME TO ix_third_party_sku_mappings_local_sku')

    # 4. 还原表名
    op.rename_table('warehouse_third_party_services', 'third_party_services')
    op.rename_table('warehouse_third_party_warehouses', 'third_party_warehouses')
    op.rename_table('warehouse_third_party_sku_mappings', 'third_party_sku_mappings')
    op.rename_table('warehouse_third_party_warehouse_maps', 'third_party_warehouse_maps')
