from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


class Warehouse(db.Model):
    """仓库表"""
    __tablename__ = 'warehouses'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(50), unique=True)
    name: Mapped[str] = mapped_column(db.String(100))
    
    # 核心分类属性
    # 1. 仓库形态: physical(实体仓) / virtual(虚拟仓)
    category: Mapped[str] = mapped_column(db.String(20), default='physical')
    
    # 2. 地理位置: domestic(国内) / overseas(海外)
    location_type: Mapped[str] = mapped_column(db.String(20), default='domestic')
    
    # 3. 管理模式: self(自营) / third_party(三方)
    ownership_type: Mapped[str] = mapped_column(db.String(20), default='self')
    
    # 仓库状态
    status: Mapped[str] = mapped_column(db.String(20), default='active')
    
    # 业务标签（用于细分监管类型，如: bonded/fba/standard）
    business_type: Mapped[str] = mapped_column(db.String(30), default='standard')
    
    # 计价币种
    currency: Mapped[str] = mapped_column(db.String(10), default='USD')
    
    # JSONB 存储第三方配置
    api_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # 虚拟仓聚合子仓列表
    child_warehouse_ids: Mapped[Optional[List[int]]] = mapped_column(ARRAY(db.Integer), nullable=True)
    
    # 物理属性
    capacity: Mapped[Optional[float]] = mapped_column(db.Numeric(12, 2), nullable=True)
    max_volume: Mapped[Optional[float]] = mapped_column(db.Numeric(12, 2), nullable=True)
    timezone: Mapped[str] = mapped_column(db.String(50), default='UTC')
    
    # 联系信息
    contact_person: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    
    # 审计字段
    created_by: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    locations: Mapped[List["WarehouseLocation"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")
    stocks: Mapped[List["WarehouseStock"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")
    stock_movements: Mapped[List["WarehouseStockMovement"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Warehouse {self.code}: {self.name}>'


class WarehouseLocation(db.Model):
    """库位表 - 用于实体仓精细化管理"""
    __tablename__ = 'warehouse_locations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(db.ForeignKey('warehouses.id'), index=True)
    
    # 库位编码
    code: Mapped[str] = mapped_column(db.String(50))
    
    # 库位类型
    type: Mapped[str] = mapped_column(db.String(20), default='storage')
    
    # 库位属性
    is_locked: Mapped[bool] = mapped_column(default=False)
    allow_mixing: Mapped[bool] = mapped_column(default=False)
    
    # 库位容量
    max_quantity: Mapped[Optional[int]] = mapped_column(nullable=True)
    max_weight: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 2), nullable=True)
    max_volume: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 2), nullable=True)
    
    # 库位状态
    status: Mapped[str] = mapped_column(db.String(20), default='available')
    
    # 审计字段
    created_by: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    warehouse: Mapped["Warehouse"] = relationship(back_populates="locations")
    stock_movements: Mapped[List["WarehouseStockMovement"]] = relationship(back_populates="location")
    
    def __repr__(self):
        return f'<WarehouseLocation {self.code} in Warehouse {self.warehouse_id}>'
