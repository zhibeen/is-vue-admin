from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.purchase.supplier import SysSupplier
from app.models.serc.enums import CustomsStatus
# Note: Product model is referenced via string "Product"

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.customs.attachment import CustomsAttachment
    from app.models.logistics.shipment import ShipmentOrder
    from app.models.user import User

class CustomsDeclaration(db.Model):
    """
    报关单 (表A/C合并)
    对应海关出口货物报关单结构
    """
    __tablename__ = "customs_declarations"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 基础信息
    pre_entry_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True, comment='预录入编号（主标识）')
    customs_no: Mapped[Optional[str]] = mapped_column(String(50), comment='海关编号/报关单单号')
    status: Mapped[str] = mapped_column(String(20), default=CustomsStatus.DRAFT.value)
    
    # 关联发货单 (发货单驱动模式)
    shipment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shipment_orders.id"), nullable=True, comment='关联发货单')
    
    # 发货人信息
    # 境内发货人 (采购主体)
    internal_shipper_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_companies.id"), comment='境内发货人ID')
    internal_shipper: Mapped["SysCompany"] = relationship("SysCompany")
    
    # 收货人信息
    overseas_consignee: Mapped[Optional[str]] = mapped_column(String(255), comment='境外收货人')
    
    # 日期与备案
    export_date: Mapped[Optional[Date]] = mapped_column(Date, comment='出口日期')
    declare_date: Mapped[Optional[Date]] = mapped_column(Date, comment='申报日期')
    filing_no: Mapped[Optional[str]] = mapped_column(String(100), comment='备案号') # 备案号
    
    # 港口与地区
    departure_port: Mapped[Optional[str]] = mapped_column(String(100), comment='出境关别/离境口岸')
    entry_port: Mapped[Optional[str]] = mapped_column(String(100), comment='进境关别') # 出口报关单通常关注出境关别
    destination_country: Mapped[Optional[str]] = mapped_column(String(100), comment='运抵国(地区)')
    trade_country: Mapped[Optional[str]] = mapped_column(String(100), comment='贸易国(地区)')
    loading_port: Mapped[Optional[str]] = mapped_column(String(100), comment='指运港')
    
    # 运输信息
    transport_mode: Mapped[Optional[str]] = mapped_column(String(50), comment='运输方式')
    conveyance_ref: Mapped[Optional[str]] = mapped_column(String(100), comment='运输工具名称及航次号')
    bill_of_lading_no: Mapped[Optional[str]] = mapped_column(String(100), comment='提运单号') # 对应 shipping_no
    
    # 贸易信息
    trade_mode: Mapped[Optional[str]] = mapped_column(String(50), comment='监管方式') # e.g., 9810
    nature_of_exemption: Mapped[Optional[str]] = mapped_column(String(50), comment='征免性质') # e.g., 101
    license_no: Mapped[Optional[str]] = mapped_column(String(50), comment='许可证号')
    contract_no: Mapped[Optional[str]] = mapped_column(String(50), comment='合同协议号')
    transaction_mode: Mapped[Optional[str]] = mapped_column(String(20), comment='成交方式') # CIF, FOB
    
    # 费用
    freight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='运费')
    insurance: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='保费')
    incidental: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='杂费')
    
    # 包装与重量
    package_type: Mapped[Optional[str]] = mapped_column(String(50), comment='包装种类')
    pack_count: Mapped[Optional[int]] = mapped_column(Integer, comment='件数')
    gross_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='毛重(千克)')
    net_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 4), comment='净重(千克)')
    
    # 备注
    marks_and_notes: Mapped[Optional[str]] = mapped_column(Text, comment='标记唛码及备注')
    documents: Mapped[Optional[str]] = mapped_column(Text, comment='随附单证')
    
    # 金额
    fob_total: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))  # USD
    currency: Mapped[Optional[str]] = mapped_column(String(10), default='USD', comment='成交币种')
    exchange_rate: Mapped[Decimal] = mapped_column(DECIMAL(10, 4))

    # 物流信息 (原有字段保留或映射)
    logistics_provider: Mapped[Optional[str]] = mapped_column(String(100), comment='物流服务商')
    # shipping_no: Mapped[Optional[str]] = mapped_column(String(100), comment='提单号/运单号') # Use bill_of_lading_no
    shipping_date: Mapped[Optional[Date]] = mapped_column(Date, comment='发货日期')
    
    # 源数据追踪
    source_type: Mapped[str] = mapped_column(String(20), default='manual', comment='来源: manual, excel_import, api')
    source_file_url: Mapped[Optional[str]] = mapped_column(String(255), comment='原始文件路径')
    
    # 货柜模式 (新增)
    container_mode: Mapped[Optional[str]] = mapped_column(String(20), default='FCL', comment='货柜模式: FCL(整柜), LCL(散货)')

    # 状态扩展与修撤
    version: Mapped[int] = mapped_column(Integer, default=1, comment='版本号')
    is_locked: Mapped[bool] = mapped_column(db.Boolean, default=False, comment='是否锁定(已生成合同)')
    amendment_reason: Mapped[Optional[str]] = mapped_column(String(255), comment='修撤原因')
    amendment_status: Mapped[Optional[str]] = mapped_column(String(20), comment='修撤审批状态')
    
    # 创建人与时间
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), comment='创建人ID')
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    items: Mapped[List["CustomsDeclarationItem"]] = relationship("CustomsDeclarationItem", back_populates="declaration")
    shipment: Mapped[Optional["ShipmentOrder"]] = relationship("ShipmentOrder", back_populates="customs_declaration")
    
    # 附件关联
    attachments: Mapped[List["CustomsAttachment"]] = relationship(
        "CustomsAttachment", 
        back_populates="declaration", 
        cascade="all, delete-orphan"
    )
    
    # 创建人关联
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])

    @property
    def product_count(self):
        return len(self.items) if self.items else 0

    @property
    def required_file_slots(self):
        """
        根据业务逻辑计算当前关单必须的文档插槽
        """
        # 1. 基础必填
        slots = ['报关单', '放行通知书', '委托报关协议', '出口退税联', '销售合同', '商业发票', '装箱单', '海运/空运提单']
        
        # 2. 判断是否为整柜 (FCL)
        is_fcl = True
        
        # 优先使用 container_mode 字段判断
        if self.container_mode:
            is_fcl = (self.container_mode.upper() == 'FCL')
        else:
            # 兼容旧数据逻辑
            if self.marks_and_notes and ('FCL' in self.marks_and_notes.upper() or '整柜' in self.marks_and_notes):
                is_fcl = True
            elif self.package_type and ('散货' in self.package_type or 'BULK' in self.package_type.upper()):
                is_fcl = False
        
        if is_fcl:
             slots.extend(['空柜照片', '铅封照片', '封柜照片', '集装箱装箱单'])
        else:
             # 3. 散货逻辑
             slots.append('散货物流发票')
             
        return slots

class CustomsDeclarationItem(db.Model):
    """
    报关单明细 (表B)
    """
    __tablename__ = "customs_declaration_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    declaration_id: Mapped[int] = mapped_column(ForeignKey("customs_declarations.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    
    # 项号
    item_no: Mapped[int] = mapped_column(Integer, comment='项号')
    
    # 商品信息
    hs_code: Mapped[Optional[str]] = mapped_column(String(20), comment='商品编号')
    product_name_spec: Mapped[Optional[str]] = mapped_column(Text, comment='商品名称及规格型号（中文）')
    product_name_en_spec: Mapped[Optional[str]] = mapped_column(Text, comment='商品英文名称及规格型号')
    
    # 数量1
    qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), comment='数量及单位1-数量 (成交数量)')
    unit: Mapped[str] = mapped_column(String(20), comment='数量及单位1-单位 (成交单位)')
    
    # 数量1 (法定第一单位) - 新增
    qty_1: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), comment='数量及单位1-法定数量')
    unit_1: Mapped[Optional[str]] = mapped_column(String(20), comment='数量及单位1-法定单位')

    # 数量2 (法定第二单位)
    qty_2: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), comment='数量及单位2-数量')
    unit_2: Mapped[Optional[str]] = mapped_column(String(20), comment='数量及单位2-单位')
    
    # 价格
    usd_unit_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 4), comment='单价')
    usd_total: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), comment='总价')
    currency: Mapped[str] = mapped_column(String(10), default='USD', comment='币制')
    
    # 原产地与目的国
    origin_country: Mapped[Optional[str]] = mapped_column(String(50), default='中国', comment='原产国(地区)')
    final_dest_country: Mapped[Optional[str]] = mapped_column(String(50), comment='最终目的国(地区)')
    district_code: Mapped[Optional[str]] = mapped_column(String(20), comment='境内货源地')
    exemption_way: Mapped[Optional[str]] = mapped_column(String(20), comment='征免') # e.g., 照章征税
    
    # 业务关联
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_suppliers.id"), nullable=True, comment='供应商ID')
    sku: Mapped[Optional[str]] = mapped_column(String(100), comment='SKU编码(冗余)')
    
    # 装箱信息 (新增)
    box_no: Mapped[Optional[str]] = mapped_column(String(50), comment='箱号')
    pack_count: Mapped[Optional[int]] = mapped_column(Integer, comment='件数（一箱多件）')
    net_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), comment='净重(KG)')
    gross_weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), comment='毛重(KG)')
    cbm: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6), comment='体积(CBM)')

    # 风控冗余字段
    rma_exchange_cost: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    
    declaration: Mapped["CustomsDeclaration"] = relationship("CustomsDeclaration", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
    supplier: Mapped["SysSupplier"] = relationship("SysSupplier")
