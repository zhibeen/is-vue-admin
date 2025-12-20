from typing import Optional, List, Dict
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, func, DECIMAL, Text, Float, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
# from app.models.serc.enums import FinAccountStatus, FinPaymentStatus

class SysPaymentTerm(db.Model):
    """付款条款配置表"""
    __tablename__ = "sys_payment_terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment='条款代码') # NET30, COD
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='条款名称') # 月结30天
    
    # 规则引擎字段
    # baseline: event_date(业务日), delivery_date(到货日), invoice_date(发票日)
    baseline: Mapped[str] = mapped_column(String(20), default='event_date', comment='基准日期')
    days_offset: Mapped[int] = mapped_column(Integer, default=0, comment='偏移天数')
    
    # 高级规则 (预留)
    # cutoff_day: Mapped[Optional[int]] = mapped_column(Integer, comment='月结关账日') 
    # type: Mapped[str] = mapped_column(String(20), default='fixed_days') # fixed_days, end_of_month
    
    def __repr__(self):
        return f"<SysPaymentTerm {self.code}>"

# -------------------------------------------------------------------------
# L2: Finance & Settlement (AP/AR)
# -------------------------------------------------------------------------

class FinSupplyContract(db.Model):
    """L2: 财务合同 (Supply) - 对应 L1 ScmDeliveryContract (一对一)"""
    __tablename__ = "fin_supply_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    l1_contract_id: Mapped[int] = mapped_column(ForeignKey("scm_delivery_contracts.id"), unique=True, nullable=False)
    
    # Snapshots from L1
    contract_no: Mapped[str] = mapped_column(String(50))
    supplier_id: Mapped[int] = mapped_column(Integer, index=True)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))
    currency: Mapped[str] = mapped_column(String(10))
    
    # Settlement Status
    # 'pending_soa' -> 'soa_generated' -> 'partially_paid' -> 'fully_paid'
    status: Mapped[str] = mapped_column(String(20), default="pending_soa")
    
    # Amounts
    reconciled_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), default=0, comment="已纳入对账单金额")
    paid_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), default=0, comment="实付金额")
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    l1_contract = relationship("ScmDeliveryContract", backref="fin_contract")
    items: Mapped[List["FinSupplyContractItem"]] = relationship(backref="supply_contract", cascade="all, delete-orphan")

class FinSupplyContractItem(db.Model):
    """L1.5: 供货合同明细 (票据视角)"""
    __tablename__ = "fin_supply_contract_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    supply_contract_id: Mapped[int] = mapped_column(ForeignKey("fin_supply_contracts.id"), nullable=False)
    
    # 聚合后的票据信息
    invoice_name: Mapped[str] = mapped_column(String(200), comment="开票品名") # 来自 Product.declared_name
    invoice_unit: Mapped[str] = mapped_column(String(20), comment="开票单位")
    specs: Mapped[Optional[str]] = mapped_column(String(200), comment="规格型号")
    
    # 量价税
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(18, 4), comment="聚合数量")
    price_unit: Mapped[Decimal] = mapped_column(DECIMAL(18, 4), comment="含税单价")
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), comment="行总价")
    
    # 税务信息
    # 来自 Supplier.default_vat_rate
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), comment="进项税率")
    # 来自 Product.tax_category.code
    tax_code: Mapped[str] = mapped_column(String(50), comment="税收分类编码") 
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

class FinPurchaseSOA(db.Model):
    """L2: 采购对账单 (Statement of Account)"""
    __tablename__ = "fin_purchase_soas"

    id: Mapped[int] = mapped_column(primary_key=True)
    soa_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    supplier_id: Mapped[int] = mapped_column(ForeignKey("sys_suppliers.id"), nullable=False)
    period_start: Mapped[Optional[Date]] = mapped_column(Date)
    period_end: Mapped[Optional[Date]] = mapped_column(Date)
    
    total_payable: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default='CNY')
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default='draft') # draft, confirmed, approved
    payment_status: Mapped[str] = mapped_column(String(20), default='unpaid') # unpaid, partial, paid
    invoice_status: Mapped[str] = mapped_column(String(20), default='none') # none, partial, full (VAT Invoice)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    supplier = relationship("SysSupplier")
    details: Mapped[List["FinPurchaseSOADetail"]] = relationship(backref="soa", cascade="all, delete-orphan")

class FinPurchaseSOADetail(db.Model):
    """L2: SOA 明细 (关联到 L1 Contract)"""
    __tablename__ = "fin_purchase_soa_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    soa_id: Mapped[int] = mapped_column(ForeignKey("fin_purchase_soas.id"), nullable=False)
    
    l1_contract_id: Mapped[int] = mapped_column(ForeignKey("scm_delivery_contracts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False, comment="本期对账金额")
    
    # Relationships
    l1_contract = relationship("ScmDeliveryContract")

# -------------------------------------------------------------------------
# L3: Payment & Treasury (Cash Flow)
# -------------------------------------------------------------------------

class FinPaymentPoolOld(db.Model):
    """
    L3: 资金池/付款计划 (Payment Schedule) - 旧版本
    
    注意：此模型已废弃，保留用于向后兼容。
    新系统请使用 app.models.serc.payable.FinPaymentPool
    """
    __tablename__ = "fin_payment_pool"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Source
    soa_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fin_purchase_soas.id"))
    # Can also be other sources like Tax, Salary, etc.
    
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default='CNY')
    
    due_date: Mapped[Optional[Date]] = mapped_column(Date, comment="预计付款日")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级 0-100")
    
    status: Mapped[str] = mapped_column(String(20), default='pending_approval') # pending_approval, approved, paying, paid
    
    # Payment Type
    type: Mapped[str] = mapped_column(String(20), default='goods') # goods, tax, logistics, salary
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    soa = relationship("FinPurchaseSOA")

class FinPaymentRequest(db.Model):
    """L3: 付款申请单 (Payment Request)"""
    __tablename__ = "fin_payment_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    request_no: Mapped[str] = mapped_column(String(50), unique=True)
    
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))
    currency: Mapped[str] = mapped_column(String(10))
    
    beneficiary_name: Mapped[str] = mapped_column(String(200))
    beneficiary_account: Mapped[str] = mapped_column(String(100))
    beneficiary_bank: Mapped[str] = mapped_column(String(100))
    
    status: Mapped[str] = mapped_column(String(20), default='pending')
    approved_by: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

class FinBankTransaction(db.Model):
    """L3: 银行流水 (Bank Transaction) - 实际资金变动"""
    __tablename__ = "fin_bank_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    trans_date: Mapped[Date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2)) # +/-
    currency: Mapped[str] = mapped_column(String(10))
    
    counterparty_name: Mapped[Optional[str]] = mapped_column(String(200))
    counterparty_account: Mapped[Optional[str]] = mapped_column(String(100))
    
    description: Mapped[Optional[str]] = mapped_column(String(500))
    reference_no: Mapped[Optional[str]] = mapped_column(String(100), comment="银行流水号")
    
    # Reconciliation status
    reconciled: Mapped[bool] = mapped_column(Integer, default=False) # 0/1
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

class FinPaymentReconcile(db.Model):
    """L3: 付款核销记录 (Payment vs SOA/Contract)"""
    __tablename__ = "fin_payment_reconciles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    transaction_id: Mapped[int] = mapped_column(ForeignKey("fin_bank_transactions.id"))
    # Target: SOA or Contract (Direct)
    soa_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fin_purchase_soas.id"))
    
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
