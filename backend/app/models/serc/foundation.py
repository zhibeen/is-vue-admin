from typing import Optional, List, Dict, Any
from sqlalchemy import String, Date, DateTime, func, DECIMAL, Text, Float, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

class SysCompany(db.Model):
    """采购主体（公司）模型"""
    __tablename__ = "sys_companies"

    # ========== 主键 ==========
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # ========== 基础信息 ==========
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False, comment='法定名称')
    short_name: Mapped[Optional[str]] = mapped_column(String(100), comment='简称')
    code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, comment='公司代码(用于单据前缀)')  # 新增字段
    english_name: Mapped[Optional[str]] = mapped_column(String(200), comment='英文名称')
    company_type: Mapped[Optional[str]] = mapped_column(String(50), comment='公司类型')
    status: Mapped[str] = mapped_column(String(20), default='active', comment='状态')
    
    # ========== 证照信息 ==========
    unified_social_credit_code: Mapped[Optional[str]] = mapped_column(String(18), unique=True, comment='统一社会信用代码')
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), comment='纳税人识别号')
    business_license_no: Mapped[Optional[str]] = mapped_column(String(50), comment='营业执照注册号')
    business_license_issue_date: Mapped[Optional[Date]] = mapped_column(Date, comment='营业执照发证日期')
    business_license_expiry_date: Mapped[Optional[Date]] = mapped_column(Date, comment='营业执照有效期')
    business_scope: Mapped[Optional[str]] = mapped_column(Text, comment='经营范围')
    
    # ========== 地址信息 ==========
    registered_address: Mapped[Optional[str]] = mapped_column(String(500), comment='注册地址')
    business_address: Mapped[Optional[str]] = mapped_column(String(500), comment='经营地址')
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), comment='邮政编码')
    
    # ========== 联系信息 ==========
    contact_person: Mapped[Optional[str]] = mapped_column(String(50), comment='联系人')
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), comment='联系电话')
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), comment='联系邮箱')
    fax: Mapped[Optional[str]] = mapped_column(String(50), comment='传真')
    
    # ========== 财务信息 ==========
    bank_accounts: Mapped[Optional[list]] = mapped_column(JSONB, comment='银行账户列表')
    tax_rate: Mapped[Optional[float]] = mapped_column(Float, comment='增值税率')
    tax_registration_date: Mapped[Optional[Date]] = mapped_column(Date, comment='税务登记日期')
    
    # ========== 跨境业务 ==========
    customs_code: Mapped[Optional[str]] = mapped_column(String(20), comment='海关编码')
    customs_registration_no: Mapped[Optional[str]] = mapped_column(String(50), comment='海关注册登记编号')
    inspection_code: Mapped[Optional[str]] = mapped_column(String(20), comment='检验检疫代码')
    foreign_trade_operator_code: Mapped[Optional[str]] = mapped_column(String(50), comment='对外贸易经营者备案号')
    forex_account: Mapped[Optional[str]] = mapped_column(String(100), comment='外汇账户')
    forex_registration_no: Mapped[Optional[str]] = mapped_column(String(50), comment='外汇登记证号')
    
    # ========== 资质证照 ==========
    import_export_license_no: Mapped[Optional[str]] = mapped_column(String(50), comment='进出口许可证号')
    import_export_license_expiry: Mapped[Optional[Date]] = mapped_column(Date, comment='进出口许可证有效期')
    special_licenses: Mapped[Optional[list]] = mapped_column(JSONB, comment='特殊资质列表')
    
    # ========== 业务配置 ==========
    default_currency: Mapped[Optional[str]] = mapped_column(String(10), default='CNY', comment='默认币种')
    default_payment_term: Mapped[Optional[str]] = mapped_column(String(50), comment='默认付款条款')
    credit_limit: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 2), comment='信用额度')
    settlement_cycle: Mapped[Optional[int]] = mapped_column(Integer, comment='结算周期（天）')
    cross_border_platform_ids: Mapped[Optional[dict]] = mapped_column(JSONB, comment='跨境平台账号')
    
    # ========== 附件与备注 ==========
    attachments: Mapped[Optional[list]] = mapped_column(JSONB, comment='附件列表')
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    
    # ========== 审计字段 ==========
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, comment='更新人ID')
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, onupdate=func.now(), comment='更新时间')
    
    def __repr__(self):
        return f"<SysCompany {self.legal_name}>"

class SysHSCode(db.Model):
    __tablename__ = "sys_hs_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200))
    refund_rate: Mapped[float] = mapped_column(DECIMAL(5, 4))  # e.g. 0.1300
    effective_date: Mapped[Optional[Date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[Date]] = mapped_column(Date)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
