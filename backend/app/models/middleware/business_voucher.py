"""
业务凭证池模型 - 数据中台核心表
统一接收来自各业务系统的数据凭证
"""
from typing import Optional
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Date, DateTime, func, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db


class FinBusinessVoucher(db.Model):
    """
    业务凭证池 - 数据中台核心表
    
    作用：
    1. 统一接收来自各业务系统（结算系统、退税系统等）的数据凭证
    2. 作为数据同步的中转站
    3. 为未来的财务总账提供数据源
    
    使用场景：
    - 结算系统：L1确认后推送凭证
    - 退税系统：报关单完成后推送凭证
    - 物流系统：发货单完成后推送物流成本凭证
    """
    __tablename__ = "fin_business_vouchers"
    
    # ========== 基础信息 ========== #
    id: Mapped[int] = mapped_column(primary_key=True)
    voucher_no: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        comment='凭证号（系统自动生成）'
    )
    voucher_date: Mapped[date] = mapped_column(
        Date, 
        nullable=False,
        comment='凭证日期'
    )
    
    # ========== 业务溯源 ========== #
    source_system: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment='来源系统（settlement=结算系统, tax=退税系统, logistics=物流系统）'
    )
    source_module: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment='来源模块（如：l1_contract, invoice, customs_declaration）'
    )
    source_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment='业务类型（如：purchase_goods, logistics_freight, tax_refund）'
    )
    source_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment='业务单据ID（如：L1的ID, 发票ID）'
    )
    source_detail_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='业务明细ID（如：L1明细ID, 可选）'
    )
    source_reference_no: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment='业务单号（如：L1-20251219-001, 便于人工查找）'
    )
    
    # ========== 业务主体 ========== #
    company_id: Mapped[int] = mapped_column(
        ForeignKey("sys_companies.id"),
        nullable=False,
        comment='采购主体/公司ID'
    )
    counterparty_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment='对方类型（supplier=供应商, customer=客户, logistics=物流商）'
    )
    counterparty_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment='对方ID'
    )
    counterparty_name: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment='对方名称（冗余字段，便于查询）'
    )
    
    # ========== 财务属性 ========== #
    direction: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        comment='借贷方向（debit=借方, credit=贷方）'
    )
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 2), 
        nullable=False,
        comment='金额'
    )
    currency: Mapped[str] = mapped_column(
        String(10), 
        default='CNY',
        comment='币种'
    )
    
    # ========== 会计科目（未来用于自动记账）========== #
    account_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment='会计科目代码（如：1403=库存商品, 6001=运费）'
    )
    account_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment='会计科目名称'
    )
    cost_center: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment='成本中心（用于成本核算）'
    )
    
    # ========== 凭证内容 ========== #
    summary: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment='凭证摘要（如：采购商品A 1000件）'
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment='详细说明'
    )
    business_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='业务数据快照（JSON格式，保存关键业务信息）'
    )
    attachment_urls: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='附件链接（如：发票扫描件、合同PDF）'
    )
    
    # ========== 状态管理 ========== #
    status: Mapped[str] = mapped_column(
        String(20), 
        default='pending',
        comment='状态（pending=待审核, approved=已审核, posted=已入账, voided=已作废）'
    )
    
    # ========== 审核信息 ========== #
    approved_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='审核人ID'
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='审核时间'
    )
    approval_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment='审核备注'
    )
    
    # ========== 总账关联（未来扩展）========== #
    gl_entry_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='总账分录ID（未来对接总账系统时使用）'
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='入账时间'
    )
    posted_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='入账人ID'
    )
    
    # ========== 数据同步状态 ========== #
    sync_status: Mapped[str] = mapped_column(
        String(20),
        default='pending',
        comment='同步状态（pending=待同步, syncing=同步中, synced=已同步, failed=失败）'
    )
    sync_target_systems: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='目标系统列表（如：["tax", "finance"]）'
    )
    synced_systems: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='已同步的系统列表'
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='最后同步时间'
    )
    
    # ========== 审计字段 ========== #
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        comment='创建时间'
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        onupdate=func.now(),
        comment='更新时间'
    )
    created_by: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment='创建人ID'
    )
    
    # ========== 索引（提升查询性能）========== #
    __table_args__ = (
        # 按来源系统和业务单据ID查询
        Index('idx_source_system_id', 'source_system', 'source_id'),
        # 按公司和日期范围查询
        Index('idx_company_date', 'company_id', 'voucher_date'),
        # 按状态和同步状态查询
        Index('idx_status_sync', 'status', 'sync_status'),
        # 按对方查询
        Index('idx_counterparty', 'counterparty_type', 'counterparty_id'),
    )
    
    def __repr__(self):
        return f"<FinBusinessVoucher(voucher_no={self.voucher_no}, amount={self.amount})>"
    
    def to_dict(self):
        """转换为字典（用于API响应和消息推送）"""
        return {
            'id': self.id,
            'voucher_no': self.voucher_no,
            'voucher_date': self.voucher_date.isoformat() if self.voucher_date else None,
            'source_system': self.source_system,
            'source_module': self.source_module,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_reference_no': self.source_reference_no,
            'company_id': self.company_id,
            'counterparty_type': self.counterparty_type,
            'counterparty_id': self.counterparty_id,
            'counterparty_name': self.counterparty_name,
            'direction': self.direction,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'summary': self.summary,
            'status': self.status,
            'sync_status': self.sync_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @staticmethod
    def generate_voucher_no():
        """生成凭证号：VCH-YYYYMMDD-序号"""
        from datetime import date as dt
        today = dt.today().strftime('%Y%m%d')
        
        # 查询今天已有的最大序号
        last_voucher = FinBusinessVoucher.query.filter(
            FinBusinessVoucher.voucher_no.like(f'VCH-{today}-%')
        ).order_by(FinBusinessVoucher.voucher_no.desc()).first()
        
        if last_voucher:
            last_seq = int(last_voucher.voucher_no.split('-')[-1])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f'VCH-{today}-{new_seq:06d}'

