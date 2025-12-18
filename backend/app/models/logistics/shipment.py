"""
发货单模型 (ShipmentOrder)
作为整个业务流程的源头，用于记录实际的货物发出信息
"""
from enum import Enum
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, func, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

# Type checking imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.serc.foundation import SysCompany
    from app.models.customs.consignee import OverseasConsignee
    from app.models.product import Product
    from app.models.customs.product import CustomsProduct
    from app.models.customs.declaration import CustomsDeclaration
    from app.models.supply.delivery import ScmDeliveryContract
    from app.models.purchase.supplier import SysSupplier


class ShipmentSource(str, Enum):
    """发货单来源"""
    MANUAL = 'manual'       # 手工创建
    EXCEL = 'excel'         # Excel导入
    LINGXING = 'lingxing'   # 领星API同步
    YICANG = 'yicang'       # 易仓API同步


class ShipmentStatus(str, Enum):
    """发货单状态"""
    DRAFT = 'draft'               # 草稿
    CONFIRMED = 'confirmed'       # 已确认
    PICKED = 'picked'             # 已拣货
    PACKED = 'packed'             # 已装箱
    SHIPPED = 'shipped'           # 已发货
    DECLARED = 'declared'         # 已报关
    COMPLETED = 'completed'       # 已完成


class ShipmentOrder(db.Model):
    """发货单主表"""
    __tablename__ = "shipment_orders"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_no: Mapped[str] = mapped_column(String(50), unique=True, comment='发货单号（唯一）')
    source: Mapped[str] = mapped_column(String(20), default=ShipmentSource.MANUAL.value, comment='来源')
    status: Mapped[str] = mapped_column(String(20), default=ShipmentStatus.DRAFT.value, comment='状态')
    
    # 外部系统数据（领星/易仓）
    external_order_no: Mapped[Optional[str]] = mapped_column(String(100), comment='外部订单号(领星/易仓)')
    external_tracking_no: Mapped[Optional[str]] = mapped_column(String(100), comment='外部跟踪号')
    external_source_data: Mapped[Optional[dict]] = mapped_column(JSONB, comment='原始数据快照')
    
    # 基本信息
    shipper_company_id: Mapped[int] = mapped_column(ForeignKey("sys_companies.id"), comment='发货公司')
    consignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customs_overseas_consignees.id"), comment='境外收货人')
    consignee_name: Mapped[Optional[str]] = mapped_column(String(255), comment='收货人名称')
    consignee_address: Mapped[Optional[str]] = mapped_column(Text, comment='收货地址')
    consignee_country: Mapped[Optional[str]] = mapped_column(String(100), comment='收货国家')
    
    # 物流信息
    logistics_provider: Mapped[Optional[str]] = mapped_column(String(100), comment='物流商')
    tracking_no: Mapped[Optional[str]] = mapped_column(String(100), comment='物流跟踪号')
    shipping_method: Mapped[Optional[str]] = mapped_column(String(50), comment='运输方式(海运/空运/快递)')
    estimated_ship_date: Mapped[Optional[Date]] = mapped_column(Date, comment='预计发货日期')
    actual_ship_date: Mapped[Optional[Date]] = mapped_column(Date, comment='实际发货日期')
    
    # 包装信息
    total_packages: Mapped[Optional[int]] = mapped_column(Integer, comment='总件数')
    total_gross_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='总毛重(kg)')
    total_net_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='总净重(kg)')
    total_volume: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='总体积(m³)')
    
    # 金额信息
    currency: Mapped[str] = mapped_column(String(10), default='USD', comment='币种')
    total_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='总金额')
    
    # 关联状态（冗余字段，方便查询）
    is_declared: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否已生成报关单')
    is_contracted: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否已生成交付合同')
    
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    # 同步信息
    last_sync_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, comment='最后同步时间')
    sync_error: Mapped[Optional[str]] = mapped_column(Text, comment='同步错误信息')
    
    # 审计字段
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, onupdate=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')
    
    # Relationships
    shipper_company: Mapped["SysCompany"] = relationship("SysCompany", foreign_keys=[shipper_company_id])
    consignee: Mapped[Optional["OverseasConsignee"]] = relationship("OverseasConsignee")
    customs_declaration: Mapped[Optional["CustomsDeclaration"]] = relationship(
        "CustomsDeclaration",
        back_populates="shipment",
        uselist=False
    )
    items: Mapped[List["ShipmentOrderItem"]] = relationship(
        "ShipmentOrderItem",
        back_populates="shipment",
        cascade="all, delete-orphan"
    )
    delivery_contracts: Mapped[List["ScmDeliveryContract"]] = relationship(
        "ScmDeliveryContract",
        back_populates="shipment",
        foreign_keys="[ScmDeliveryContract.shipment_id]"
    )


class ShipmentOrderItem(db.Model):
    """发货单明细表"""
    __tablename__ = "shipment_order_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipment_orders.id"), nullable=False)
    
    # 产品信息
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), comment='系统产品ID')
    sku: Mapped[str] = mapped_column(String(100), comment='SKU')
    product_name: Mapped[str] = mapped_column(String(255), comment='商品名称')
    product_name_en: Mapped[Optional[str]] = mapped_column(String(255), comment='英文品名')
    
    # 归类信息
    hs_code: Mapped[Optional[str]] = mapped_column(String(20), comment='HS编码')
    customs_product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customs_products.id"), comment='归类商品ID')
    
    # 数量信息
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), comment='数量')
    unit: Mapped[str] = mapped_column(String(20), default='PCS', comment='单位')
    
    # 价格信息
    unit_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='单价')
    total_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='总价')
    
    # 重量信息
    unit_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), comment='单件重量(kg)')
    total_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='总重量(kg)')
    
    # 原产地
    origin_country: Mapped[Optional[str]] = mapped_column(String(100), comment='原产国')
    
    # 外部系统商品ID
    external_item_id: Mapped[Optional[str]] = mapped_column(String(100), comment='外部商品ID')
    
    # 供应商信息（用于按供应商拆分生成交付合同）
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_suppliers.id"), comment='供应商ID')
    
    # Relationships
    shipment: Mapped["ShipmentOrder"] = relationship("ShipmentOrder", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product")
    customs_product: Mapped[Optional["CustomsProduct"]] = relationship("CustomsProduct")
    supplier: Mapped[Optional["SysSupplier"]] = relationship("SysSupplier")

