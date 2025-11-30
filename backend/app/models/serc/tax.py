from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from .enums import TaxInvoiceStatus, CustomsStatus

class SysExchangeRate(db.Model):
    """
    汇率风控配置
    """
    __tablename__ = "sys_exchange_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    currency: Mapped[str] = mapped_column(String(10), unique=True)  # USD
    rate: Mapped[Decimal] = mapped_column(DECIMAL(10, 4))
    safe_min: Mapped[Decimal] = mapped_column(DECIMAL(10, 4))
    safe_max: Mapped[Decimal] = mapped_column(DECIMAL(10, 4))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class TaxInvoice(db.Model):
    """
    进项发票 (表G)
    """
    __tablename__ = "tax_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_code: Mapped[str] = mapped_column(String(50))
    invoice_no: Mapped[str] = mapped_column(String(50), unique=True)
    
    amount_total: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))  # 价税合计
    tax_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))
    
    soa_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fin_purchase_soas.id"))
    status: Mapped[str] = mapped_column(String(20), default=TaxInvoiceStatus.FREE.value)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    soa: Mapped["FinPurchaseSOA"] = relationship("FinPurchaseSOA")
    items: Mapped[List["TaxInvoiceItem"]] = relationship("TaxInvoiceItem", back_populates="invoice")

class TaxInvoiceItem(db.Model):
    __tablename__ = "tax_invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("tax_invoices.id"))
    
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(20))
    qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 4))
    price: Mapped[Decimal] = mapped_column(DECIMAL(18, 4))  # 含税单价
    total: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))
    
    invoice: Mapped["TaxInvoice"] = relationship("TaxInvoice", back_populates="items")

class TaxCustomsDeclaration(db.Model):
    """
    报关单 (表A/C合并)
    """
    __tablename__ = "tax_customs_declarations"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    status: Mapped[str] = mapped_column(String(20), default=CustomsStatus.DRAFT.value)
    
    export_date: Mapped[Optional[Date]] = mapped_column(Date)
    destination_country: Mapped[Optional[str]] = mapped_column(String(100))
    
    fob_total: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))  # USD
    exchange_rate: Mapped[Decimal] = mapped_column(DECIMAL(10, 4))
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    items: Mapped[List["TaxCustomsItem"]] = relationship("TaxCustomsItem", back_populates="declaration")

class TaxCustomsItem(db.Model):
    """
    报关单明细 (表B)
    """
    __tablename__ = "tax_customs_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    declaration_id: Mapped[int] = mapped_column(ForeignKey("tax_customs_declarations.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    
    qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 4))
    unit: Mapped[str] = mapped_column(String(20))
    usd_unit_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 4))
    usd_total: Mapped[Decimal] = mapped_column(DECIMAL(18, 2))
    
    # 风控冗余字段
    rma_exchange_cost: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    
    declaration: Mapped["TaxCustomsDeclaration"] = relationship("TaxCustomsDeclaration", back_populates="items")
    product: Mapped["Product"] = relationship("Product")

class TaxRefundMatch(db.Model):
    """
    关联匹配表 (表D)
    """
    __tablename__ = "tax_refund_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    customs_item_id: Mapped[int] = mapped_column(ForeignKey("tax_customs_items.id"))
    invoice_item_id: Mapped[int] = mapped_column(ForeignKey("tax_invoice_items.id"))
    
    matched_qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 4))
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    customs_item: Mapped["TaxCustomsItem"] = relationship("TaxCustomsItem")
    invoice_item: Mapped["TaxInvoiceItem"] = relationship("TaxInvoiceItem")

