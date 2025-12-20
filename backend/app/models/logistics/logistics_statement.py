"""
物流对账单和付款单模型
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING, List
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, Text, func, Table, Column, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from app.extensions import db

if TYPE_CHECKING:
    from app.models.logistics.shipment import ShipmentOrder
    from app.models.logistics.logistics_provider import LogisticsProvider
    from app.models.logistics.shipment_logistics_service import ShipmentLogisticsService
    from app.models.auth import User


class StatementStatus(str, Enum):
    """对账单状态"""
    DRAFT = 'draft'          # 草稿
    CONFIRMED = 'confirmed'  # 已确认（物流主管）
    SUBMITTED = 'submitted'  # 已提交财务
    APPROVED = 'approved'    # 财务已批准
    PAID = 'paid'            # 已付款


class PaymentStatus(str, Enum):
    """付款单状态（已废弃，保留以兼容旧数据）"""
    PENDING = 'pending'      # 待审批
    APPROVED = 'approved'    # 已审批
    PAID = 'paid'            # 已付款


# 对账单-物流服务关联表（多对多中间表）
statement_service_relation = Table(
    'statement_service_relations',
    db.metadata,
    Column('statement_id', Integer, ForeignKey('logistics_statements.id', ondelete='CASCADE'), primary_key=True),
    Column('logistics_service_id', Integer, ForeignKey('shipment_logistics_services.id'), primary_key=True),
    Column('reconciled_amount', DECIMAL(18, 2), nullable=False, comment='本次对账金额'),
    Column('created_at', DateTime, server_default=func.now())
)


class LogisticsStatement(db.Model):
    """物流对账单表 - 业务侧对账记录"""
    __tablename__ = "logistics_statements"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    statement_no: Mapped[str] = mapped_column(String(50), unique=True, comment='对账单号')
    
    # ========== 对账范围 ========== #
    logistics_provider_id: Mapped[int] = mapped_column(
        ForeignKey("logistics_providers.id"), 
        comment='物流服务商ID'
    )
    statement_period_start: Mapped[date] = mapped_column(Date, comment='对账周期-开始')
    statement_period_end: Mapped[date] = mapped_column(Date, comment='对账周期-结束')
    
    # ========== 对账金额 ========== #
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), comment='对账总额')
    currency: Mapped[str] = mapped_column(
        String(10), 
        default='CNY', 
        server_default='CNY',
        comment='币种'
    )
    
    # ========== 业务确认（物流跟单负责）========== #
    status: Mapped[str] = mapped_column(
        String(20), 
        default=StatementStatus.DRAFT.value,
        server_default='draft',
        comment='状态'
    )
    confirmed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), 
        comment='业务确认人(物流专员)'
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='确认时间')
    
    # ========== 财务关联（提交后生成）========== #
    finance_payable_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='关联财务应付单ID（SERC）'
    )
    submitted_to_finance_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='提交财务时间'
    )
    
    # ========== 附件与备注 ========== #
    attachment_ids: Mapped[Optional[List[int]]] = mapped_column(
        JSON,
        comment='对账单附件ID列表（凭证中心）'
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    # ========== 向后兼容字段（已废弃）========== #
    shipment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='[DEPRECATED] 发货单ID，新版本使用多对多关联'
    )
    statement_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment='[DEPRECATED] 对账日期，使用 statement_period_end'
    )
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment='[DEPRECATED] 付款方式，由财务模块管理'
    )
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')
    
    # Relationships
    logistics_provider: Mapped["LogisticsProvider"] = relationship("LogisticsProvider")
    confirmed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[confirmed_by_id])
    
    # 关联的物流服务明细（多对多）
    logistics_services: Mapped[List["ShipmentLogisticsService"]] = relationship(
        "ShipmentLogisticsService",
        secondary=statement_service_relation,
        backref="statements"
    )
    
    def __repr__(self):
        return f"<LogisticsStatement {self.statement_no} - {self.logistics_provider.provider_name if self.logistics_provider else 'N/A'}>"


class LogisticsPayment(db.Model):
    """
    物流付款单表（已废弃）
    
    注意：此表保留用于数据兼容，新系统使用财务模块的 FinPayable 统一管理所有付款。
    迁移路径：LogisticsPayment → FinPayable (source_type='logistics')
    """
    __tablename__ = "logistics_payments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    payment_no: Mapped[str] = mapped_column(String(50), unique=True, comment='付款单号')
    statement_id: Mapped[int] = mapped_column(ForeignKey("logistics_statements.id"), comment='对账单ID')
    
    payment_date: Mapped[Optional[date]] = mapped_column(Date, comment='付款日期')
    payment_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(18, 2), comment='付款金额')
    currency: Mapped[str] = mapped_column(String(10), default='CNY', server_default='CNY', comment='币种')
    payment_pool_id: Mapped[Optional[int]] = mapped_column(Integer, comment='付款池ID')
    
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PENDING.value, server_default='pending', comment='状态')
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), comment='审批人ID')
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='审批时间')
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='付款时间')
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
    
    # Relationships
    statement: Mapped["LogisticsStatement"] = relationship("LogisticsStatement")
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])

