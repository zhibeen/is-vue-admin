from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.serc.enums import SourceDocType, ContractStatus
# Type checking imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.purchase.supplier import SysSupplier
    from app.models.serc.foundation import SysCompany
    from app.models.product import Product
    from app.models.serc.finance import SysPaymentTerm

class ScmSourceDoc(db.Model):
    __tablename__ = "scm_source_docs"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20))  # Enum: SourceDocType
    supplier_id: Mapped[int] = mapped_column(ForeignKey("sys_suppliers.id"))
    event_date: Mapped[Date] = mapped_column(Date)
    
    # External tracing: {"sys": "LX", "po": "PO001"}
    tracking_source: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    supplier: Mapped["SysSupplier"] = relationship("SysSupplier")

class ScmDeliveryContract(db.Model):
    __tablename__ = "scm_delivery_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    source_doc_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scm_source_docs.id"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("sys_suppliers.id"))
    
    # Added company_id (purchasing entity)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_companies.id"))
    
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    status: Mapped[str] = mapped_column(String(20), default=ContractStatus.PENDING.value)
    
    # Cache fields for payment tracking
    paid_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), default=0)

    # Added fields
    delivery_address: Mapped[Optional[str]] = mapped_column(String(255), comment='交付地点')
    delivery_date: Mapped[Optional[Date]] = mapped_column(Date, comment='送货日期')
    notes: Mapped[Optional[str]] = mapped_column(String(500), comment='合同备注')
    
    # 供应商快照（固化签约时的供应商信息，如名称、地址、税号、开户行等）
    supplier_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, comment='供应商快照')
    
    # 财务信息
    payment_term_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_payment_terms.id"), comment='付款条款ID')
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), comment='付款条款(快照)')
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), comment='付款方式')
    
    # 乐观锁版本控制
    version: Mapped[int] = mapped_column(Integer, default=0, comment='乐观锁版本号')
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    source_doc: Mapped["ScmSourceDoc"] = relationship("ScmSourceDoc")
    supplier: Mapped["SysSupplier"] = relationship("SysSupplier")
    company: Mapped["SysCompany"] = relationship("SysCompany") # Added relationship
    payment_term: Mapped["SysPaymentTerm"] = relationship("SysPaymentTerm")
    items: Mapped[List["ScmDeliveryContractItem"]] = relationship("ScmDeliveryContractItem", back_populates="contract", cascade="all, delete-orphan")

class ScmDeliveryContractItem(db.Model):
    __tablename__ = "scm_delivery_contract_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    l1_contract_id: Mapped[int] = mapped_column(ForeignKey("scm_delivery_contracts.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    
    confirmed_qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 4))
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 4))  # Tax included
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))
    
    # Added notes field
    notes: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Relationships
    contract: Mapped["ScmDeliveryContract"] = relationship("ScmDeliveryContract", back_populates="items")
    product: Mapped["Product"] = relationship("Product")

class ScmContractChangeLog(db.Model):
    """合同变更日志表"""
    __tablename__ = "scm_contract_change_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("scm_delivery_contracts.id"), nullable=False)
    
    changed_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    changed_by: Mapped[Optional[int]] = mapped_column(Integer, comment='操作人ID')
    change_type: Mapped[str] = mapped_column(String(50), default='update') 
    change_reason: Mapped[Optional[str]] = mapped_column(String(255))
    
    # 存储变更前后的关键数据快照
    content_before: Mapped[dict] = mapped_column(JSONB)
    content_after: Mapped[dict] = mapped_column(JSONB)
    
    contract: Mapped["ScmDeliveryContract"] = relationship("ScmDeliveryContract")
