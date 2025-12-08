from typing import Optional, List, Dict, Any, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, DateTime, func, Text, Integer, ForeignKey, Numeric, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class SysSupplier(db.Model):
    """供应商模型 (SRM)"""
    __tablename__ = "sys_suppliers"

    # ========== 主键与编码 ==========
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='供应商代码')
    
    # ========== 基础信息 ==========
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment='供应商名称')
    short_name: Mapped[Optional[str]] = mapped_column(String(100), comment='简称')
    supplier_type: Mapped[str] = mapped_column(String(50), default='manufacturer', comment='类型')
    status: Mapped[str] = mapped_column(String(20), default='active', comment='状态')
    grade: Mapped[Optional[str]] = mapped_column(String(10), comment='等级')
    
    # ========== 联系信息 ==========
    country: Mapped[Optional[str]] = mapped_column(String(50), comment='国家/地区')
    province: Mapped[Optional[str]] = mapped_column(String(50), comment='省份')
    city: Mapped[Optional[str]] = mapped_column(String(50), comment='城市')
    address: Mapped[Optional[str]] = mapped_column(String(500), comment='详细地址')
    website: Mapped[Optional[str]] = mapped_column(String(200), comment='官网')
    
    primary_contact: Mapped[Optional[str]] = mapped_column(String(50), comment='首要联系人')
    primary_phone: Mapped[Optional[str]] = mapped_column(String(50), comment='联系电话')
    primary_email: Mapped[Optional[str]] = mapped_column(String(100), comment='Email')
    
    # 联系人列表 [{"name": "...", "role": "...", "phone": "..."}]
    contacts: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=[], comment='联系人列表')

    # ========== 财务信息 ==========
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), comment='税号/VAT号')
    currency: Mapped[str] = mapped_column(String(10), default='CNY', comment='默认结算币种')
    
    # OLD: payment_terms = mapped_column(String(100))
    # NEW: Link to SysPaymentTerm
    payment_term_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_payment_terms.id"), comment='默认付款条款ID')
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), comment='付款条款(旧字段/快照)') # Keep as fallback/snapshot

    payment_method: Mapped[Optional[str]] = mapped_column(String(50), comment='付款方式')
    
    # 纳税人属性
    taxpayer_type: Mapped[Optional[str]] = mapped_column(String(20), comment='纳税人类型: general(一般), small(小规模)')
    default_vat_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), comment='默认开票税率')
    
    # 银行账户列表 [{"bank_name": "...", "account": "...", "currency": "..."}]
    bank_accounts: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=[], comment='银行账户')

    # ========== 运营参数 ==========
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer, comment='平均交货天数')
    moq: Mapped[Optional[str]] = mapped_column(String(50), comment='最小起订量描述')
    
    # ========== 管理信息 ==========
    purchase_uid: Mapped[Optional[int]] = mapped_column(Integer, comment='负责采购员ID')
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')
    tags: Mapped[List[str]] = mapped_column(JSONB, default=[], comment='标签')
    
    # ========== 审计 ==========
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, onupdate=func.now())
    
    if TYPE_CHECKING:
        from app.models.serc.finance import SysPaymentTerm

    # Relationships
    payment_term: Mapped["SysPaymentTerm"] = relationship("SysPaymentTerm")

    @property
    def payment_term_name(self):
        """优先返回结构化条款名称，否则返回文本快照"""
        if self.payment_term:
            return self.payment_term.name
        return self.payment_terms

    def __repr__(self):
        return f"<SysSupplier {self.name}>"
