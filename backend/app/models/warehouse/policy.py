from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional


class WarehouseProductGroup(db.Model):
    """
    (v1.3 新增) 仓库专用 SKU 分组 (SKU团)
    用于库存分配策略的中间层颗粒度，例如 "2025黑五促销组"
    """
    __tablename__ = 'warehouse_product_groups'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(50), unique=True)
    name: Mapped[str] = mapped_column(db.String(100))
    # 备注说明
    note: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<WarehouseProductGroup {self.code}>'


class WarehouseProductGroupItem(db.Model):
    """(v1.3 新增) SKU 分组明细"""
    __tablename__ = 'warehouse_product_group_items'
    
    group_id: Mapped[int] = mapped_column(db.ForeignKey('warehouse_product_groups.id'), primary_key=True)
    sku: Mapped[str] = mapped_column(db.String(50), primary_key=True)


class StockAllocationPolicy(db.Model):
    """
    (v1.3 新增) 统一库存分配策略表
    优先级逻辑：SKU > Group > Category > Warehouse
    """
    __tablename__ = 'stock_allocation_policies'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 策略目标: 哪个虚拟仓/团队受益？
    virtual_warehouse_id: Mapped[int] = mapped_column(db.ForeignKey('warehouses.id'), index=True)
    
    # 策略范围 (四选一，决定颗粒度)
    # Level 1: 全局 (仅填 source_warehouse_id)
    # Level 2: 品类 (填 category_id)
    # Level 2.5: SKU团 (填 warehouse_product_group_id)
    # Level 3: 单品 (填 sku)
    source_warehouse_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouses.id'), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)     # 关联产品分类表
    warehouse_product_group_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouse_product_groups.id'), nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)

    # 规则配置
    ratio: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)   # 分配比例 (如 0.8)
    fixed_amount: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True) # 锁定量 (如 100)
    priority: Mapped[int] = mapped_column(db.Integer, default=0) # 抢货权重 (KPI高的优先)

    # 继承/覆盖标志
    # override: 强制覆盖低级规则
    policy_mode: Mapped[str] = mapped_column(db.String(20), default='override')

    def __repr__(self):
        return f'<StockAllocationPolicy {self.id}>'

