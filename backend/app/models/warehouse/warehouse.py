from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.warehouse.stock import WarehouseStock


class Warehouse(db.Model):
    """仓库表"""
    __tablename__ = 'warehouses'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(50), unique=True)
    name: Mapped[str] = mapped_column(db.String(100))
    
    # 核心分类属性 (v1.3 重构)
    # 1. 仓库形态: physical(实体仓) / virtual(虚拟仓)
    category: Mapped[str] = mapped_column(db.String(20), default='physical')
    
    # 2. 地理位置: domestic(国内) / overseas(海外)
    location_type: Mapped[str] = mapped_column(db.String(20), default='domestic')
    
    # 3. 管理模式: self(自营) / third_party(三方)
    ownership_type: Mapped[str] = mapped_column(db.String(20), default='self')
    
    # 仓库状态 (Status 枚举)
    # planning: 筹备中 (采购可见，销售不可见)
    # active: 正常 (全功能开启)
    # suspended: 暂停/整顿 (限制入库，允许出库，用于FBA/海外仓异常)
    # clearing: 清退中 (禁止入库，允许出库，用于结束合作)
    # deprecated: 已废弃 (历史保留，默认隐藏)
    status: Mapped[str] = mapped_column(db.String(20), default='active')
    
    # 业务标签（用于细分监管类型，如: bonded/fba/standard）
    business_type: Mapped[str] = mapped_column(db.String(30), default='standard')
    
    # 计价币种
    currency: Mapped[str] = mapped_column(db.String(10), default='USD')
    
    # JSONB 存储第三方配置
    # 建议结构: {"external_warehouse_code": "US-WEST-01", "sync_rule": "hourly"}
    # 认证信息存储在 ThirdPartyService 表中
    api_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # (v1.3 新增) 关联第三方服务商
    third_party_service_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouse_third_party_services.id'), nullable=True)
    third_party_service = relationship('WarehouseThirdPartyService', backref='warehouses')
    
    # (v1.4 新增) 关联具体的第三方仓库 (持久化表)
    # 取代原有的 api_config['external_warehouse_code']
    third_party_warehouse_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouse_third_party_warehouses.id'), nullable=True)
    third_party_warehouse = relationship('WarehouseThirdPartyWarehouse', backref='bound_local_warehouses')

    # (v1.3 新增) 虚拟仓聚合子仓列表
    # 仅当 category='virtual' 且用于聚合统计时使用 (如: 美国总仓 = [美东仓ID, 美西仓ID])
    child_warehouse_ids: Mapped[Optional[List[int]]] = mapped_column(ARRAY(db.Integer), nullable=True)
    
    # 物理属性
    capacity: Mapped[Optional[float]] = mapped_column(db.Numeric(12, 2), nullable=True)
    max_volume: Mapped[Optional[float]] = mapped_column(db.Numeric(12, 2), nullable=True)
    timezone: Mapped[str] = mapped_column(db.String(50), default='UTC')
    
    # 联系信息 (保留，文档未提及但实用)
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
    # stock_movements 关系通常在 movement 侧维护外键，这里反向引用可选
    # stock_movements: Mapped[List["WarehouseStockMovement"]] = relationship(back_populates="warehouse")
    
    def __repr__(self):
        return f'<Warehouse {self.code}: {self.name}>'


class WarehouseLocation(db.Model):
    """库位表 - 用于实体仓精细化管理"""
    __tablename__ = 'warehouse_locations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(db.ForeignKey('warehouses.id'), index=True)
    
    # 库位编码 (如: A-01-01-01 区-排-层-位)
    code: Mapped[str] = mapped_column(db.String(50))
    
    # 库位类型 (storage:存储, pick:拣货, receive:收货, return:退货, stage:暂存)
    type: Mapped[str] = mapped_column(db.String(20), default='storage')
    
    # 库位属性 (用于上架策略)
    is_locked: Mapped[bool] = mapped_column(default=False)
    allow_mixing: Mapped[bool] = mapped_column(default=False)  # 是否允许混放SKU
    
    warehouse: Mapped["Warehouse"] = relationship(back_populates="locations")

    def __repr__(self):
        return f'<Location {self.code}>'
