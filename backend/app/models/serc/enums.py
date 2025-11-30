from enum import Enum

class SourceDocType(str, Enum):
    PL_EXPORT = "PL_EXPORT"
    GRN_STOCK = "GRN_STOCK"
    MANUAL = "MANUAL"  # 手工录入

class ContractStatus(str, Enum):
    PENDING = "pending"   # 待结算
    SETTLING = "settling" # 结算中
    SETTLED = "settled"   # 已结算

class SettlementStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"

class InvoiceStatus(str, Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"

class PaymentPoolStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"

class PaymentType(str, Enum):
    DEPOSIT = "deposit"   # 定金
    BALANCE = "balance"   # 尾款
    PREPAY = "prepay"     # 预付
    TAX = "tax"           # 税金

class TaxInvoiceStatus(str, Enum):
    FREE = "free"         # 游离
    RESERVED = "reserved" # 预占
    LOCKED = "locked"     # 已申报

class CustomsStatus(str, Enum):
    DRAFT = "draft"
    PRE_DECLARED = "pre_declared"
    OFFICIAL = "official"

