"""
开票合同模型 (ScmSupplyContract)
用于记录财务开票信息，与交付合同形成"双轨制"
关键约束：delivery_contract_id 必须唯一（严格1对1关系）
"""
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, func, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

# Type checking imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.supply.delivery import ScmDeliveryContract
    from app.models.purchase.supplier import SysSupplier
    from app.models.finance.tax_invoice import SupplierTaxInvoice


class ScmSupplyContract(db.Model):
    """开票合同 - 财务开票凭证"""
    __tablename__ = "scm_supply_contracts"
    
    # 表级约束：确保严格1对1关系
    __table_args__ = (
        UniqueConstraint('delivery_contract_id', name='uk_delivery_contract_id'),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contract_no: Mapped[str] = mapped_column(String(50), unique=True, comment='开票合同号（唯一）')
    
    # 关联交付合同（1对1，唯一约束）
    delivery_contract_id: Mapped[int] = mapped_column(
        ForeignKey("scm_delivery_contracts.id"),
        nullable=False,
        comment='主交付合同ID（1对1唯一）'
    )
    
    # 供应商信息
    supplier_id: Mapped[int] = mapped_column(ForeignKey("sys_suppliers.id"), nullable=False)
    
    # 金额信息（必须与交付合同一致）
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False, comment='总金额（不含税）')
    currency: Mapped[str] = mapped_column(String(10), default="CNY", comment='币种')
    
    # 税务信息
    tax_rate: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), comment='税率(如0.13)')
    total_amount_with_tax: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 2),
        comment='含税总额'
    )
    
    # 状态信息
    status: Mapped[str] = mapped_column(String(20), comment='合同状态')
    invoice_status: Mapped[str] = mapped_column(
        String(20),
        default='uninvoiced',
        comment='开票状态: uninvoiced/partial/invoiced'
    )
    
    # 开票金额追踪
    invoiced_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 2), 
        default=0,
        comment='已开票金额'
    )
    
    # 开票说明（如果调整了品名/数量，必填）
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='开票说明')
    
    # 合同日期
    contract_date: Mapped[Date] = mapped_column(Date, comment='合同日期')
    
    # 审计字段
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, onupdate=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')
    
    # Relationships
    delivery_contract: Mapped["ScmDeliveryContract"] = relationship(
        "ScmDeliveryContract",
        back_populates="supply_contract"
    )
    supplier: Mapped["SysSupplier"] = relationship("SysSupplier")
    items: Mapped[List["ScmSupplyContractItem"]] = relationship(
        "ScmSupplyContractItem",
        back_populates="contract",
        cascade="all, delete-orphan"
    )
    invoices: Mapped[List["SupplierTaxInvoice"]] = relationship(
        "SupplierTaxInvoice",
        back_populates="supply_contract"
    )


class ScmSupplyContractItem(db.Model):
    """开票合同明细 - 开票商品（可能与实际商品不同）"""
    __tablename__ = "scm_supply_contract_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("scm_supply_contracts.id"), nullable=False)
    
    # 开票商品信息（可能与实际商品不同）
    product_name: Mapped[str] = mapped_column(String(255), comment='开票商品名称')
    specification: Mapped[Optional[str]] = mapped_column(String(255), comment='规格型号')
    
    # 数量信息
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), comment='数量')
    unit: Mapped[str] = mapped_column(String(20), comment='开票单位(台/套/箱)')
    
    # 价格信息
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 4), comment='单价（不含税）')
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), comment='小计（不含税）')
    
    # 税额
    tax_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), comment='税额')
    
    # 溯源信息（关联到真实的交付合同明细）
    source_delivery_item_ids: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='源交付合同明细ID列表(用于溯源)'
    )
    
    # Relationships
    contract: Mapped["ScmSupplyContract"] = relationship("ScmSupplyContract", back_populates="items")

