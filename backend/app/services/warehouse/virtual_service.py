from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
from app.extensions import db
from app.models.warehouse import (
    Warehouse, WarehouseStock, StockAllocationPolicy, WarehouseProductGroup, WarehouseProductGroupItem
)
from app.errors import BusinessError
import logging

logger = logging.getLogger(__name__)


class VirtualService:
    """虚拟仓服务"""
    
    def __init__(self):
        pass
    
    def get_virtual_stock(self, virtual_warehouse_id: int, sku: str) -> Dict[str, Any]:
        """
        计算虚拟仓库存
        逻辑：
        1. 找到虚拟仓对应的分配策略 (Global, Category, Group, SKU)
        2. 根据策略找到源仓库 (Source Warehouse)
        3. 获取源仓库的物理库存 (Physical Stock)
        4. 应用分配规则 (Ratio, Fixed) 计算虚拟库存
        """
        # 1. 获取分配策略 (按优先级排序: SKU > Group > Category > Warehouse)
        # 这里简化处理，实际应该是一个复杂的查找过程，或者在数据库层面做视图
        # 目前先只支持 SKU 级和 Warehouse 级策略
        
        # 查找 SKU 级策略
        policy = db.session.execute(
            select(StockAllocationPolicy).where(
                and_(
                    StockAllocationPolicy.virtual_warehouse_id == virtual_warehouse_id,
                    StockAllocationPolicy.sku == sku
                )
            )
        ).scalar_one_or_none()
        
        if not policy:
            # 查找 Warehouse 级策略 (Source Warehouse)
            policy = db.session.execute(
                select(StockAllocationPolicy).where(
                    and_(
                        StockAllocationPolicy.virtual_warehouse_id == virtual_warehouse_id,
                        StockAllocationPolicy.source_warehouse_id.isnot(None),
                        StockAllocationPolicy.sku.is_(None),
                        StockAllocationPolicy.category_id.is_(None),
                        StockAllocationPolicy.warehouse_product_group_id.is_(None)
                    )
                )
            ).scalar_one_or_none()
            
        if not policy:
            return {'sku': sku, 'quantity': 0, 'virtual_warehouse_id': virtual_warehouse_id}
            
        # 2. 获取源仓库库存
        if not policy.source_warehouse_id:
            # 如果没有指定源仓库，可能是一个纯逻辑的虚拟仓，或者策略配置错误
            return {'sku': sku, 'quantity': 0, 'virtual_warehouse_id': virtual_warehouse_id}
            
        source_stock = db.session.execute(
            select(WarehouseStock).where(
                and_(
                    WarehouseStock.warehouse_id == policy.source_warehouse_id,
                    WarehouseStock.sku == sku
                )
            )
        ).scalar_one_or_none()
        
        if not source_stock:
            return {'sku': sku, 'quantity': 0, 'virtual_warehouse_id': virtual_warehouse_id}
            
        # 3. 计算虚拟库存
        base_qty = source_stock.available_quantity # 默认基于可用库存
        
        virtual_qty = 0
        if policy.ratio is not None:
            virtual_qty = int(base_qty * policy.ratio)
        elif policy.fixed_amount is not None:
            virtual_qty = min(base_qty, policy.fixed_amount) # 不能超过物理库存
        else:
            virtual_qty = base_qty # 默认 100%
            
        return {
            'sku': sku,
            'quantity': virtual_qty,
            'virtual_warehouse_id': virtual_warehouse_id,
            'source_warehouse_id': policy.source_warehouse_id,
            'policy_id': policy.id
        }

    def _get_stocks_by_sku(self, sku: str, warehouse_id: Optional[int] = None) -> List[WarehouseStock]:
        """Helper to get stocks"""
        query = select(WarehouseStock).where(WarehouseStock.sku == sku)
        
        if warehouse_id:
            query = query.where(WarehouseStock.warehouse_id == warehouse_id)
            
        return db.session.execute(query).scalars().all()

    def _get_stocks_by_group(self, group_id: int, warehouse_id: Optional[int] = None) -> List[WarehouseStock]:
        """Helper to get stocks by group"""
        # 1. Get SKUs in group
        group_items = select(WarehouseProductGroupItem.sku).where(
            WarehouseProductGroupItem.group_id == group_id
        )
        
        # 2. Get Stocks
        query = select(WarehouseStock).where(WarehouseStock.sku.in_(group_items))
        
        if warehouse_id:
            query = query.where(WarehouseStock.warehouse_id == warehouse_id)
            
        return db.session.execute(query).scalars().all()
