from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class WarehouseThirdPartyService(db.Model):
    """(v1.3 新增) 第三方服务商配置表 (用于存放认证信息)"""
    __tablename__ = 'warehouse_third_party_services'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(50), unique=True) # 如: winit, goodcang
    name: Mapped[str] = mapped_column(db.String(100))
    provider_code: Mapped[str] = mapped_column(db.String(50), default='4px') # 供应商代码: 4px, winit, cne
    
    # 认证信息 (加密存储)
    api_url: Mapped[str] = mapped_column(db.String(255))
    app_key: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    app_secret: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    
    # 状态
    is_active: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(db.String(20), default='unknown') # connected, auth_failed, unknown
    last_sync_time: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    
    # 配置模版
    config_template: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    def __repr__(self):
        return f'<WarehouseThirdPartyService {self.code}>'


class WarehouseThirdPartyWarehouseMap(db.Model):
    """(v1.5 新增) 三方仓库与本地仓库关联表"""
    __tablename__ = 'warehouse_third_party_warehouse_maps'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 关联
    service_id: Mapped[int] = mapped_column(db.ForeignKey('warehouse_third_party_services.id'))
    
    # 远程信息
    remote_code: Mapped[str] = mapped_column(db.String(50))
    remote_name: Mapped[str] = mapped_column(db.String(100))
    
    # 本地关联 (可为空，表示只是拉取到了但未绑定)
    local_warehouse_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouses.id'), nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('service_id', 'remote_code', name='uix_service_remote_wh'),
    )


class WarehouseThirdPartyWarehouse(db.Model):
    """(v1.4 新增) 三方仓库表 - 持久化存储远端仓库列表"""
    __tablename__ = 'warehouse_third_party_warehouses'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 归属服务商
    service_id: Mapped[int] = mapped_column(db.ForeignKey('warehouse_third_party_services.id'), index=True)
    service = relationship('WarehouseThirdPartyService', backref='warehouses_list')
    
    # 三方原始数据
    code: Mapped[str] = mapped_column(db.String(50))  # 第三方代码 (如: WPGA4)
    name: Mapped[str] = mapped_column(db.String(100)) # 第三方名称
    country_code: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True) # 国家 (如: US)
    
    # 系统状态
    is_active: Mapped[bool] = mapped_column(default=False) # 默认禁用，需手动开启
    note: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    
    # 同步状态
    last_synced_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # 联合唯一索引：同一个服务商下 code 唯一
    __table_args__ = (
        db.UniqueConstraint('service_id', 'code', name='uix_service_warehouse_code'),
    )

    def __repr__(self):
        return f'<WarehouseThirdPartyWarehouse {self.code}>'


class WarehouseThirdPartyProduct(db.Model):
    """
    (v1.8 新增) 三方商品源数据表
    用于存储从海外仓拉取下来的所有商品信息，作为"未配对"数据的来源
    """
    __tablename__ = 'warehouse_third_party_products'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 归属服务商
    service_id: Mapped[int] = mapped_column(db.ForeignKey('warehouse_third_party_services.id'), index=True)
    
    # 商品核心信息
    remote_sku: Mapped[str] = mapped_column(db.String(100), index=True) # 三方 SKU
    remote_name: Mapped[str] = mapped_column(db.String(200))           # 三方商品名称
    
    # 规格信息 (可选)
    specs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True) # 长宽高重等
    image_url: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    
    # 同步状态
    last_synced_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 联合唯一索引
    __table_args__ = (
        db.UniqueConstraint('service_id', 'remote_sku', name='uix_service_remote_sku'),
    )

    def __repr__(self):
        return f'<WarehouseThirdPartyProduct {self.remote_sku}>'


class WarehouseThirdPartySkuMapping(db.Model):
    """
    (v1.4 新增) 三方 SKU 映射表
    支持 Level 2 (服务商级) 和 Level 3 (仓库级)
    """
    __tablename__ = 'warehouse_third_party_sku_mappings'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 作用域：如果 warehouse_id 为空，则是 Level 2 (服务商全局)；否则是 Level 3 (仓库特例)
    service_id: Mapped[int] = mapped_column(db.ForeignKey('warehouse_third_party_services.id'), index=True)
    warehouse_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('warehouse_third_party_warehouses.id'), nullable=True)
    
    # 映射关系
    remote_sku: Mapped[str] = mapped_column(db.String(100), index=True) # 三方 SKU
    local_sku: Mapped[str] = mapped_column(db.String(100), index=True)  # 本地 SKU
    
    # 比例关系 (用于组合/拆分，默认 1.0)
    # 场景：三方 1个 Box = 本地 10个 Pcs
    quantity_ratio: Mapped[float] = mapped_column(db.Float, default=1.0)
    
    # 优先级 (用于多对一场景，数字越小优先级越高)
    priority: Mapped[int] = mapped_column(db.Integer, default=0)
    
    # 关系 (反向引用)
    warehouse = relationship('WarehouseThirdPartyWarehouse')
    
    __table_args__ = (
        # 索引优化：查询某服务商某 SKU 的映射
        db.Index('idx_mapping_lookup', 'service_id', 'remote_sku', 'warehouse_id'),
    )

    def __repr__(self):
        return f'<WarehouseSKUMapping {self.remote_sku} -> {self.local_sku}>'
