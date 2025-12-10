from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List


class WarehouseProductGroup(db.Model):
    """仓库专用 SKU 分组"""
    __tablename__ = 'warehouse_product_groups'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(50), unique=True)
    name: Mapped[str] = mapped_column(db.String(100))
    note: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    
    # 审计字段
    created_by: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    items: Mapped[List["WarehouseProductGroupItem"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    allocation_policies: Mapped[List["StockAllocationPolicy"]] = relationship(back_populates="product_group")
    
    def __repr__(self):
        return f'<WarehouseProductGroup {self.code}: {self.name}>'


class WarehouseProductGroupItem(db.Model):
    """SKU 分组明细"""
    __tablename__ = 'warehouse_product_group_items'
    
    group_id: Mapped[int] = mapped_column(db.ForeignKey('warehouse_product_groups.id'), primary_key=True)
    sku: Mapped[str] = mapped_column(db.String(50), primary_key=True)
    
    # 审计字段
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # 关系
    group: Mapped["WarehouseProductGroup"] = relationship(back_populates="items")
    
    def __repr__(self):
        return f'<WarehouseProductGroupItem {self.sku} in Group {self.group_id}>'


class StockAllocationPolicy(db.Model):
    """统一库存分配策略表"""
    __tablename__ = 'stock_allocation_policies'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 策略目标: 哪个虚拟仓/团队受益？
    virtual_warehouse_id: Mapped[int] = mapped_column(db.ForeignKey('warehouses.id'), index=True)
    
    # 策略范围
    source_warehouse_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouses.id'), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    warehouse_product_group_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouse_product_groups.id'), nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    
    # 规则配置
    ratio: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    fixed_amount: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    priority: Mapped[int] = mapped_column(db.Integer, default=0)
    
    # 继承/覆盖标志
    policy_mode: Mapped[str] = mapped_column(db.String(20), default='override')
    
    # 生效时间
    effective_from: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # 审计字段
    created_by: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    virtual_warehouse: Mapped["Warehouse"] = relationship(foreign_keys=[virtual_warehouse_id])
    source_warehouse: Mapped[Optional["Warehouse"]] = relationship(foreign_keys=[source_warehouse_id])
    product_group: Mapped[Optional["WarehouseProductGroup"]] = relationship(back_populates="allocation_policies")
    
    def __repr__(self):
        return f'<StockAllocationPolicy {self.id}: {self.virtual_warehouse_id}>'
