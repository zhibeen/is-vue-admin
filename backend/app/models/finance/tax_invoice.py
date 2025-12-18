"""
供应商增值税发票模型 (SupplierTaxInvoice)
用于记录供应商开具的增值税专用发票信息
与开票合同(ScmSupplyContract)关联
"""
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

# Type checking imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.supply.supply_contract import ScmSupplyContract
    from app.models.purchase.supplier import SysSupplier


class SupplierTaxInvoice(db.Model):
    """供应商发票（与开票合同关联）"""
    __tablename__ = "supplier_tax_invoices"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_no: Mapped[str] = mapped_column(String(50), unique=True, comment='发票号码（唯一）')
    invoice_code: Mapped[str] = mapped_column(String(50), comment='发票代码')
    
    # 关联开票合同
    supply_contract_id: Mapped[int] = mapped_column(
        ForeignKey("scm_supply_contracts.id"),
        nullable=False,
        comment='关联开票合同'
    )
    
    # 供应商
    supplier_id: Mapped[int] = mapped_column(ForeignKey("sys_suppliers.id"), nullable=False)
    
    # 金额信息
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False, comment='不含税金额')
    tax_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False, comment='税额')
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False, comment='价税合计')
    
    # 发票类型
    invoice_type: Mapped[str] = mapped_column(
        String(20),
        comment='special/ordinary/electronic'
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20),
        default='valid',
        comment='valid/cancelled/invalid'
    )
    
    # 日期信息
    invoice_date: Mapped[Date] = mapped_column(Date, nullable=False, comment='开票日期')
    received_date: Mapped[Optional[Date]] = mapped_column(Date, comment='收票日期')
    
    # 附件
    attachment_url: Mapped[Optional[str]] = mapped_column(String(255), comment='发票扫描件')
    
    # 审计字段
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, onupdate=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')
    
    # Relationships
    supply_contract: Mapped["ScmSupplyContract"] = relationship(
        "ScmSupplyContract",
        back_populates="invoices"
    )
    supplier: Mapped["SysSupplier"] = relationship("SysSupplier")

