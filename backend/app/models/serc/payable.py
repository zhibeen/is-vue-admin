"""
财务应付单和付款池模型
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, Text, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from app.extensions import db

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.document.document import DocumentCenter


class PayableSourceType(str, Enum):
    """应付单来源类型"""
    SUPPLY_CONTRACT = 'supply_contract'     # 供货合同
    LOGISTICS = 'logistics'                 # 物流对账
    EXPENSE = 'expense'                     # 费用报销
    OTHER = 'other'                         # 其他


class PayableStatus(str, Enum):
    """应付单状态"""
    PENDING = 'pending'          # 待审批
    APPROVED = 'approved'        # 已批准
    IN_POOL = 'in_pool'         # 在付款池中
    PAID = 'paid'               # 已付款
    REJECTED = 'rejected'       # 已驳回
    CANCELLED = 'cancelled'     # 已取消


class PaymentPoolStatus(str, Enum):
    """付款池状态"""
    DRAFT = 'draft'             # 草稿
    PENDING = 'pending'         # 待审批
    APPROVED = 'approved'       # 已批准
    PROCESSING = 'processing'   # 付款中
    COMPLETED = 'completed'     # 已完成
    CANCELLED = 'cancelled'     # 已取消


class FinPayable(db.Model):
    """财务应付单表（统一管理所有应付款）"""
    __tablename__ = "fin_payables"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    payable_no: Mapped[str] = mapped_column(String(50), unique=True, comment='应付单号')
    
    # ========== 来源信息 ========== #
    source_type: Mapped[str] = mapped_column(
        String(20),
        comment='来源类型（supply_contract/logistics/expense）'
    )
    source_id: Mapped[int] = mapped_column(Integer, comment='来源单据ID')
    source_no: Mapped[Optional[str]] = mapped_column(String(50), comment='来源单号')
    
    # ========== 收款方信息 ========== #
    payee_type: Mapped[str] = mapped_column(
        String(20), 
        comment='收款方类型（supplier/logistics_provider/employee）'
    )
    payee_id: Mapped[int] = mapped_column(Integer, comment='收款方ID')
    payee_name: Mapped[str] = mapped_column(String(200), comment='收款方名称')
    
    # 银行信息（冗余存储，方便付款）
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), comment='开户银行')
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), comment='银行账号')
    bank_account_name: Mapped[Optional[str]] = mapped_column(String(100), comment='账户名称')
    
    # ========== 金额信息 ========== #
    payable_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), comment='应付金额')
    paid_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 2),
        default=Decimal('0'),
        server_default='0',
        comment='已付金额'
    )
    currency: Mapped[str] = mapped_column(
        String(10), 
        default='CNY',
        server_default='CNY',
        comment='币种'
    )
    
    # ========== 付款计划 ========== #
    due_date: Mapped[Optional[date]] = mapped_column(Date, comment='应付日期')
    priority: Mapped[int] = mapped_column(
        Integer, 
        default=3,
        server_default='3',
        comment='优先级(1-最高, 5-最低)'
    )
    
    # ========== 审批流程 ========== #
    status: Mapped[str] = mapped_column(
        String(20),
        default=PayableStatus.PENDING.value,
        server_default='pending',
        comment='状态'
    )
    approved_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), 
        comment='审批人'
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='审批时间')
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, comment='驳回原因')
    
    # ========== 付款执行 ========== #
    payment_pool_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("fin_payment_pools.id"),
        comment='付款池ID'
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='付款时间')
    payment_voucher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_center.id"),
        comment='付款凭证ID'
    )
    
    # ========== 备注 ========== #
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')
    
    # Relationships
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])
    payment_pool: Mapped[Optional["FinPaymentPool"]] = relationship("FinPaymentPool", back_populates="payables")
    payment_voucher: Mapped[Optional["DocumentCenter"]] = relationship("DocumentCenter")
    
    def __repr__(self):
        return f"<FinPayable {self.payable_no} - {self.payee_name} ¥{self.payable_amount}>"
    
    @property
    def remaining_amount(self) -> Decimal:
        """剩余未付金额"""
        return self.payable_amount - self.paid_amount
    
    @property
    def is_fully_paid(self) -> bool:
        """是否已全额付款"""
        return self.paid_amount >= self.payable_amount


class FinPaymentPool(db.Model):
    """付款池表（批量付款管理）"""
    __tablename__ = "fin_payment_pools"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    pool_no: Mapped[str] = mapped_column(String(50), unique=True, comment='付款池编号')
    pool_name: Mapped[str] = mapped_column(String(200), comment='付款池名称')
    
    # ========== 批次信息 ========== #
    scheduled_date: Mapped[date] = mapped_column(Date, comment='计划付款日期')
    total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 2),
        default=Decimal('0'),
        server_default='0',
        comment='总金额'
    )
    total_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default='0',
        comment='应付单数量'
    )
    
    # ========== 状态管理 ========== #
    status: Mapped[str] = mapped_column(
        String(20),
        default=PaymentPoolStatus.DRAFT.value,
        server_default='draft',
        comment='状态'
    )
    
    # ========== 审批信息 ========== #
    approved_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        comment='审批人'
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='审批时间')
    
    # ========== 执行信息 ========== #
    executed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        comment='执行人（出纳）'
    )
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='执行时间')
    
    # ========== 备注 ========== #
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')
    
    # Relationships
    payables: Mapped[list["FinPayable"]] = relationship(
        "FinPayable",
        back_populates="payment_pool",
        foreign_keys="[FinPayable.payment_pool_id]"
    )
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])
    executed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[executed_by_id])
    
    def __repr__(self):
        return f"<FinPaymentPool {self.pool_no} - {self.pool_name}>"

