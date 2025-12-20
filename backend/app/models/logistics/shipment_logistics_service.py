"""
发货单物流服务明细模型 (ShipmentLogisticsService)
记录一个发货单对应的多个物流服务商及其费用

【重要说明】：
- 费用采用手工录入方式（物流服务商无API接口）
- estimated_amount: 预估费用（发货前由跟单人员根据报价录入）
- actual_amount: 实际费用（收到账单后由财务人员录入）
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.extensions import db

if TYPE_CHECKING:
    from app.models.logistics.shipment import ShipmentOrder
    from app.models.logistics.logistics_provider import LogisticsProvider
    from app.models.document.document_center import DocumentCenter


class ServiceStatus(str, Enum):
    """服务状态"""
    PENDING = 'pending'          # 待确认
    CONFIRMED = 'confirmed'      # 已确认
    RECONCILED = 'reconciled'    # 已对账
    PAID = 'paid'                # 已付款


class ShipmentLogisticsService(db.Model):
    """发货单物流服务明细表"""
    __tablename__ = "shipment_logistics_services"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 关联
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipment_orders.id", ondelete="CASCADE"),
        comment='发货单ID'
    )
    logistics_provider_id: Mapped[int] = mapped_column(
        ForeignKey("logistics_providers.id"),
        comment='物流服务商ID'
    )
    
    # 服务信息
    service_type: Mapped[str] = mapped_column(String(50), comment='服务类型')
    service_description: Mapped[Optional[str]] = mapped_column(Text, comment='服务描述')
    
    # 费用信息
    estimated_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(18, 2), 
        comment='预估费用'
    )
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(18, 2), 
        comment='实际费用'
    )
    currency: Mapped[str] = mapped_column(
        String(10), 
        default='CNY',
        server_default='CNY',
        comment='币种'
    )
    payment_method: Mapped[Optional[str]] = mapped_column(String(20), comment='付款方式')
    
    # 凭证关联
    service_voucher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_center.id"), 
        comment='服务凭证ID'
    )
    payment_voucher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_center.id"), 
        comment='付款凭证ID'
    )
    
    # 状态与时间
    status: Mapped[str] = mapped_column(
        String(20), 
        default=ServiceStatus.PENDING.value,
        server_default='pending',
        comment='状态'
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='确认时间')
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='对账时间')
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='付款时间')
    
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    # 审计字段
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
    
    # Relationships
    shipment: Mapped["ShipmentOrder"] = relationship(
        "ShipmentOrder", 
        back_populates="logistics_services"
    )
    logistics_provider: Mapped["LogisticsProvider"] = relationship("LogisticsProvider")
    service_voucher: Mapped[Optional["DocumentCenter"]] = relationship(
        "DocumentCenter", 
        foreign_keys=[service_voucher_id]
    )
    payment_voucher: Mapped[Optional["DocumentCenter"]] = relationship(
        "DocumentCenter", 
        foreign_keys=[payment_voucher_id]
    )
    
    def __repr__(self):
        return f"<ShipmentLogisticsService {self.id}: Shipment {self.shipment_id} - {self.service_type}>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'logistics_provider_id': self.logistics_provider_id,
            'logistics_provider_name': self.logistics_provider.provider_name if self.logistics_provider else None,
            'service_type': self.service_type,
            'service_description': self.service_description,
            'estimated_amount': float(self.estimated_amount) if self.estimated_amount else None,
            'actual_amount': float(self.actual_amount) if self.actual_amount else None,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'service_voucher_id': self.service_voucher_id,
            'payment_voucher_id': self.payment_voucher_id,
            'status': self.status,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'reconciled_at': self.reconciled_at.isoformat() if self.reconciled_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

