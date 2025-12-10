#!/usr/bin/env python3
"""测试仓库模型导入"""

import sys
import os

print("开始测试仓库模型导入...")

# 添加项目路径
sys.path.insert(0, '/app')

try:
    print("尝试导入模型...")
    from app.models.warehouse import Warehouse, WarehouseLocation, Stock, StockMovement
    from app.models.warehouse import StockDiscrepancy, WarehouseProductGroup, WarehouseProductGroupItem, StockAllocationPolicy
    
    print("✅ 仓库模型导入成功!")
    print(f"Warehouse: {Warehouse}")
    print(f"WarehouseLocation: {WarehouseLocation}")
    print(f"Stock: {Stock}")
    print(f"StockMovement: {StockMovement}")
    print(f"StockDiscrepancy: {StockDiscrepancy}")
    print(f"WarehouseProductGroup: {WarehouseProductGroup}")
    print(f"WarehouseProductGroupItem: {WarehouseProductGroupItem}")
    print(f"StockAllocationPolicy: {StockAllocationPolicy}")
    
    # 检查表名
    print("\n✅ 表名检查:")
    print(f"Warehouse.__tablename__: {Warehouse.__tablename__}")
    print(f"WarehouseLocation.__tablename__: {WarehouseLocation.__tablename__}")
    print(f"Stock.__tablename__: {Stock.__tablename__}")
    print(f"StockMovement.__tablename__: {StockMovement.__tablename__}")
    print(f"StockDiscrepancy.__tablename__: {StockDiscrepancy.__tablename__}")
    print(f"WarehouseProductGroup.__tablename__: {WarehouseProductGroup.__tablename__}")
    print(f"WarehouseProductGroupItem.__tablename__: {WarehouseProductGroupItem.__tablename__}")
    print(f"StockAllocationPolicy.__tablename__: {StockAllocationPolicy.__tablename__}")
    
    print("\n✅ 所有模型导入测试通过!")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()

print("测试完成。")
