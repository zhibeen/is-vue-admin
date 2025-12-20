"""
物流服务商模型 (LogisticsProvider)
用于管理物流服务商主数据，区别于商品供应商
"""
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Boolean, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.extensions import db


class LogisticsServiceType(str, Enum):
    """物流服务类型"""
    DOMESTIC_TRUCKING = 'domestic_trucking'    # 国内卡车运输
    INTERNATIONAL_SEA = 'international_sea'    # 国际海运
    INTERNATIONAL_AIR = 'international_air'    # 国际空运
    CUSTOMS_CLEARANCE = 'customs_clearance'    # 清关服务
    DESTINATION_DELIVERY = 'destination_delivery'  # 目的国派送


class PaymentMethodType(str, Enum):
    """付款方式"""
    PREPAID = 'prepaid'      # 预付
    IMMEDIATE = 'immediate'  # 即付
    POSTPAID = 'postpaid'    # 后付


class SettlementCycle(str, Enum):
    """结算周期"""
    IMMEDIATE = 'immediate'  # 即时结算
    WEEKLY = 'weekly'        # 周结
    MONTHLY = 'monthly'      # 月结


class LogisticsProvider(db.Model):
    """物流服务商表"""
    __tablename__ = "logistics_providers"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 基本信息
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False, comment='服务商名称')
    provider_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='服务商编码')
    
    # 服务类型
    service_type: Mapped[Optional[str]] = mapped_column(String(50), comment='服务类型')
    
    # 付款与结算
    payment_method: Mapped[Optional[str]] = mapped_column(String(20), comment='付款方式')
    settlement_cycle: Mapped[Optional[str]] = mapped_column(String(20), comment='结算周期')
    
    # 联系信息
    contact_name: Mapped[Optional[str]] = mapped_column(String(50), comment='联系人')
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), comment='联系电话')
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), comment='邮箱')
    
    # 银行信息
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), comment='开户银行')
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), comment='银行账号')
    bank_account_name: Mapped[Optional[str]] = mapped_column(String(100), comment='账户名称')
    
    # 服务区域（支持多个）
    service_areas: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), comment='服务区域')
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true', comment='启用状态')
    
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    # 审计字段
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
    
    def __repr__(self):
        return f"<LogisticsProvider {self.provider_code}: {self.provider_name}>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'provider_name': self.provider_name,
            'provider_code': self.provider_code,
            'service_type': self.service_type,
            'payment_method': self.payment_method,
            'settlement_cycle': self.settlement_cycle,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'bank_name': self.bank_name,
            'bank_account': self.bank_account,
            'bank_account_name': self.bank_account_name,
            'service_areas': self.service_areas,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
