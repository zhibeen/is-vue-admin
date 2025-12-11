from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


class WarehouseStock(db.Model):
    """
    库存余额表 (聚合视图)
    注意：对于实体仓，这是仓库级总库存。
    """
    __tablename__ = 'stocks' # 注意：表名调整为 stocks (文档v1.3建议) 或者保持 warehouse_stocks
    # 为了保持与文档一致，建议使用 stocks，但如果已有 warehouse_stocks，改名需谨慎。
    # 这里我们跟随文档 v1.3 使用 stocks。如果项目规范是加前缀，请自行调整。
    # 鉴于 is-vue-admin 规范通常是复数，这里用 stocks。
    __tablename__ = 'stocks'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(db.String(50), index=True)
    warehouse_id: Mapped[int] = mapped_column(db.ForeignKey('warehouses.id'))
    
    # 库存数量
    physical_quantity: Mapped[int] = mapped_column(default=0)
    available_quantity: Mapped[int] = mapped_column(default=0)
    allocated_quantity: Mapped[int] = mapped_column(default=0)
    in_transit_quantity: Mapped[int] = mapped_column(default=0)
    damaged_quantity: Mapped[int] = mapped_column(default=0)
    
    # 批次信息
    batch_no: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    
    # 汽配特性：冗余体积重量数据
    weight: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    volume: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    
    # 乐观锁版本号
    version: Mapped[int] = mapped_column(default=0)
    
    # 关系
    warehouse: Mapped["Warehouse"] = relationship(back_populates="stocks")
    
    def __repr__(self):
        return f'<Stock {self.sku} @ {self.warehouse_id}: {self.available_quantity}>'


class WarehouseStockMovement(db.Model):
    """库存单据/流水表"""
    __tablename__ = 'stock_movements'

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(db.String(50), index=True)
    warehouse_id: Mapped[int] = mapped_column(db.ForeignKey('warehouses.id'))
    
    # 关联库位 (v1.3 新增)
    location_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouse_locations.id'), nullable=True)

    # 单据基础信息
    order_type: Mapped[str] = mapped_column(db.String(30))  # inbound/outbound/transfer/adjustment
    order_no: Mapped[str] = mapped_column(db.String(50), index=True)
    biz_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 变更数量
    quantity_delta: Mapped[int] = mapped_column()

    # 关联批次与成本信息
    batch_no: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(db.Numeric(18, 4), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    
    # 汇率快照 (v1.3 新增)
    exchange_rate: Mapped[Decimal] = mapped_column(db.Numeric(10, 4), default=1.0)

    # 审计字段
    created_by: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    status: Mapped[str] = mapped_column(db.String(20), default='confirmed')


class WarehouseStockDiscrepancy(db.Model):
    """库存差异记录表 (用于第三方仓对账与风控告警)"""
    __tablename__ = 'stock_discrepancies'

    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(db.ForeignKey('warehouses.id'))
    sku: Mapped[str] = mapped_column(db.String(50))

    local_qty: Mapped[int] = mapped_column()
    remote_qty: Mapped[int] = mapped_column()

    # 差异强度
    diff_ratio: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    diff_amount: Mapped[Optional[Decimal]] = mapped_column(db.Numeric(18, 4), nullable=True)

    # 状态与处理信息
    status: Mapped[str] = mapped_column(default='pending')  # pending/resolved/ignored
    discovered_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    resolver_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
