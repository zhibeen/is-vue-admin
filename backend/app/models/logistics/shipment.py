"""
发货单模型 (ShipmentOrder)
作为整个业务流程的源头，用于记录实际的货物发出信息
"""
from enum import Enum
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, func, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
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
    from app.models.logistics.purchase_item import ShipmentPurchaseItem
    from app.models.logistics.shipment_logistics_service import ShipmentLogisticsService


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
    
    # ========== 仓库信息 ========== #
    # 发货仓库
    origin_warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, comment='发货仓库ID')
    origin_warehouse_name: Mapped[Optional[str]] = mapped_column(String(100), comment='发货仓库名称')
    origin_warehouse_type: Mapped[Optional[str]] = mapped_column(String(20), comment='发货仓库类型(self/factory/supplier)')
    origin_warehouse_address: Mapped[Optional[str]] = mapped_column(Text, comment='发货仓库地址')
    is_factory_direct: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否工厂直发')
    
    # 收货仓库
    destination_warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, comment='收货仓库ID')
    destination_warehouse_name: Mapped[Optional[str]] = mapped_column(String(100), comment='收货仓库名称')
    destination_warehouse_code: Mapped[Optional[str]] = mapped_column(String(50), comment='收货仓库编码')
    destination_warehouse_type: Mapped[Optional[str]] = mapped_column(String(20), comment='仓库类型(fba/third_party/self)')
    destination_warehouse_address: Mapped[Optional[str]] = mapped_column(Text, comment='收货仓库地址')
    
    # FBA专用字段
    fba_shipment_id: Mapped[Optional[str]] = mapped_column(String(100), comment='FBA发货计划ID')
    fba_center_codes: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), comment='FBA中心编码数组')
    marketplace: Mapped[Optional[str]] = mapped_column(String(10), comment='市场站点(US/UK/DE/JP等)')
    
    # 第三方仓专用字段
    warehouse_service_provider: Mapped[Optional[str]] = mapped_column(String(100), comment='仓储服务商')
    warehouse_contact: Mapped[Optional[str]] = mapped_column(String(50), comment='仓库联系人')
    warehouse_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), comment='仓库联系电话')
    
    # ========== 物流信息 ========== #
    logistics_provider: Mapped[Optional[str]] = mapped_column(String(100), comment='物流商')
    logistics_service_type: Mapped[Optional[str]] = mapped_column(String(50), comment='物流服务类型')
    tracking_no: Mapped[Optional[str]] = mapped_column(String(100), comment='物流跟踪号')
    shipping_method: Mapped[Optional[str]] = mapped_column(String(50), comment='运输方式(air/sea/express/land/sea_air)')
    freight_term: Mapped[Optional[str]] = mapped_column(String(20), comment='运费支付方式(prepaid/collect/third_party)')
    
    # 时间节点
    estimated_ship_date: Mapped[Optional[Date]] = mapped_column(Date, comment='预计发货日期')
    actual_ship_date: Mapped[Optional[Date]] = mapped_column(Date, comment='实际发货日期')
    estimated_arrival_date: Mapped[Optional[Date]] = mapped_column(Date, comment='预计到货日期')
    actual_arrival_date: Mapped[Optional[Date]] = mapped_column(Date, comment='实际到货日期')
    warehouse_received_date: Mapped[Optional[DateTime]] = mapped_column(DateTime, comment='仓库签收时间')
    completed_date: Mapped[Optional[DateTime]] = mapped_column(DateTime, comment='完成时间')
    
    # ========== 包装信息 ========== #
    total_packages: Mapped[Optional[int]] = mapped_column(Integer, comment='总件数')
    packing_method: Mapped[Optional[str]] = mapped_column(String(50), comment='包装方式(纸箱/托盘/散装)')
    total_gross_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='总毛重(kg)')
    total_net_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='总净重(kg)')
    total_volume: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='总体积(m³)')
    volumetric_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment='体积重(kg)')
    chargeable_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment='计费重量(kg)')
    
    # ========== 金额与财务信息 ========== #
    currency: Mapped[str] = mapped_column(String(10), default='USD', comment='币种')
    
    # ===== 物流成本（核心字段，保留） ===== #
    freight_cost: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='运费')
    insurance_cost: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='保险费')
    handling_fee: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='操作费')
    other_costs: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='其他费用')
    total_logistics_cost: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='物流总成本')
    
    # ===== 以下字段标记为废弃，将在v2.0移除 ===== #
    # @deprecated - 应从商品明细实时计算
    total_goods_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='货物总价值 [DEPRECATED: 从商品明细计算]')
    declared_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='申报价值 [DEPRECATED: 从报关单获取]')
    
    # @deprecated - 应从财务系统获取
    vat_number: Mapped[Optional[str]] = mapped_column(String(50), comment='VAT税号 [DEPRECATED: 从公司/收货人主表获取]')
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 4), comment='税率 [DEPRECATED: 从税务配置获取]')
    estimated_tax: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='预估税费 [DEPRECATED: 从税务系统获取]')
    actual_tax: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='实际税费 [DEPRECATED: 从税务系统获取]')
    
    # @deprecated - 应从采购明细计算
    total_purchase_cost: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='采购总成本 [DEPRECATED: 从采购明细汇总]')
    
    # @deprecated - 应从财务系统动态计算
    profit_margin: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 2), comment='利润率(%) [DEPRECATED: 从财务系统计算]')
    cost_allocation_method: Mapped[Optional[str]] = mapped_column(String(20), comment='成本分摊方式 [DEPRECATED: 从财务配置获取]')
    
    # @deprecated - 向后兼容字段，仅供参考
    total_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='总金额（不含税）[DEPRECATED: 从采购明细计算]')
    total_tax_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='总税额 [DEPRECATED: 从报关单获取]')
    total_amount_with_tax: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='含税总金额 [DEPRECATED: 从采购+报关单计算]')
    
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
    purchase_items: Mapped[List["ShipmentPurchaseItem"]] = relationship(
        "ShipmentPurchaseItem",
        back_populates="shipment_order",
        cascade="all, delete-orphan",
        order_by="ShipmentPurchaseItem.id"
    )
    delivery_contracts: Mapped[List["ScmDeliveryContract"]] = relationship(
        "ScmDeliveryContract",
        back_populates="shipment",
        foreign_keys="[ScmDeliveryContract.shipment_id]"
    )
    logistics_services: Mapped[List["ShipmentLogisticsService"]] = relationship(
        "ShipmentLogisticsService",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="ShipmentLogisticsService.id"
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
    export_name: Mapped[Optional[str]] = mapped_column(String(255), comment='出口申报名称')
    customs_product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customs_products.id"), comment='归类商品ID')
    
    # 数量信息
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), comment='数量')
    unit: Mapped[str] = mapped_column(String(20), default='PCS', comment='单位')
    customs_unit: Mapped[Optional[str]] = mapped_column(String(20), comment='海关申报单位')
    
    # 价格信息（不含税）
    unit_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='单价（不含税）')
    total_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='总价（不含税）')
    
    # 税务信息
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 4), comment='税率(如0.13表示13%)')
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='税额')
    unit_price_with_tax: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='含税单价')
    total_price_with_tax: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='含税总价')
    
    # 采购信息
    purchase_order_id: Mapped[Optional[int]] = mapped_column(Integer, comment='采购单ID')
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_suppliers.id"), comment='主供应商ID')
    supplier_name: Mapped[Optional[str]] = mapped_column(String(100), comment='主供应商名称')
    
    # ========== FBA专用字段 ========== #
    fnsku: Mapped[Optional[str]] = mapped_column(String(50), comment='亚马逊FNSKU')
    msku: Mapped[Optional[str]] = mapped_column(String(100), comment='商家SKU(MSKU)')
    asin: Mapped[Optional[str]] = mapped_column(String(20), comment='ASIN码')
    marketplace_listing_id: Mapped[Optional[str]] = mapped_column(String(100), comment='市场Listing ID')
    
    # ========== 第三方仓专用字段 ========== #
    warehouse_matched_qty: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), comment='配对数量')
    warehouse_received_qty: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), comment='已收数量')
    warehouse_pending_qty: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), comment='待收数量')
    shelf_location: Mapped[Optional[str]] = mapped_column(String(50), comment='货架位置')
    
    # ========== 包装信息 ========== #
    package_no: Mapped[Optional[str]] = mapped_column(String(50), comment='箱号')
    barcode: Mapped[Optional[str]] = mapped_column(String(100), comment='箱码/条码')
    
    # 重量体积
    unit_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), comment='单件重量(kg)')
    unit_volume: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6), comment='单件体积(m³)')
    total_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='总重量(kg)')
    
    # 原产地
    origin_country: Mapped[Optional[str]] = mapped_column(String(100), comment='原产国')
    
    # 外部系统商品ID
    external_item_id: Mapped[Optional[str]] = mapped_column(String(100), comment='外部商品ID')
    
    # Relationships
    shipment: Mapped["ShipmentOrder"] = relationship("ShipmentOrder", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product")
    customs_product: Mapped[Optional["CustomsProduct"]] = relationship("CustomsProduct")
    supplier: Mapped[Optional["SysSupplier"]] = relationship("SysSupplier")

