"""
凭证管理中心模型 (DocumentCenter)
通用的业务凭证管理，支持物流/采购/报关/付款四大类凭证
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.extensions import db

if TYPE_CHECKING:
    from app.models.auth import User


class BusinessType(str, Enum):
    """业务类型"""
    LOGISTICS = 'logistics'      # 物流业务
    PURCHASE = 'purchase'        # 采购业务
    CUSTOMS = 'customs'          # 报关业务
    PAYMENT = 'payment'          # 付款业务


class DocumentCategory(str, Enum):
    """文档分类"""
    SERVICE_VOUCHER = 'service_voucher'    # 服务凭证
    PAYMENT_VOUCHER = 'payment_voucher'    # 付款凭证
    CONTRACT_VOUCHER = 'contract_voucher'  # 合同凭证
    INVOICE_VOUCHER = 'invoice_voucher'    # 发票凭证
    CUSTOMS_VOUCHER = 'customs_voucher'    # 报关凭证


class AuditStatus(str, Enum):
    """审核状态"""
    PENDING = 'pending'      # 待审核
    APPROVED = 'approved'    # 已审核
    REJECTED = 'rejected'    # 已驳回


class DocumentCenter(db.Model):
    """凭证管理中心表"""
    __tablename__ = "document_center"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 业务关联（多态关联）
    business_type: Mapped[str] = mapped_column(String(30), nullable=False, comment='业务类型')
    document_type: Mapped[Optional[str]] = mapped_column(String(50), comment='凭证类型')
    document_category: Mapped[Optional[str]] = mapped_column(String(30), comment='文档分类')
    business_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='业务单据ID')
    business_no: Mapped[Optional[str]] = mapped_column(String(100), comment='业务单据编号')
    
    # 文件信息
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment='文件名')
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment='文件路径')
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, comment='文件大小(bytes)')
    file_type: Mapped[Optional[str]] = mapped_column(String(20), comment='文件扩展名')
    file_url: Mapped[Optional[str]] = mapped_column(String(500), comment='可访问URL')
    
    # 上传信息
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, comment='上传人ID')
    uploaded_at: Mapped[datetime] = mapped_column(nullable=False, comment='上传时间')
    
    # 审核信息
    audit_status: Mapped[str] = mapped_column(String(20), server_default='pending', nullable=False, comment='审核状态')
    audited_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), comment='审核人ID')
    audited_at: Mapped[Optional[datetime]] = mapped_column(comment='审核时间')
    audit_notes: Mapped[Optional[str]] = mapped_column(Text, comment='审核备注')
    
    # 归档信息
    archived: Mapped[bool] = mapped_column(Boolean, server_default='false', default=False, comment='是否已归档')
    archive_path: Mapped[Optional[str]] = mapped_column(String(500), comment='归档路径')
    archived_at: Mapped[Optional[datetime]] = mapped_column(comment='归档时间')
    
    # 审计字段
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
    
    # Relationships
    uploaded_by: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by_id])
    audited_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[audited_by_id])
    
    def __repr__(self):
        return f"<DocumentCenter {self.id}: {self.business_type}-{self.business_no} ({self.file_name})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'business_type': self.business_type,
            'document_type': self.document_type,
            'document_category': self.document_category,
            'business_id': self.business_id,
            'business_no': self.business_no,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'file_url': self.file_url,
            'uploaded_by_id': self.uploaded_by_id,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'audit_status': self.audit_status,
            'audited_by_id': self.audited_by_id,
            'audited_at': self.audited_at.isoformat() if self.audited_at else None,
            'audit_notes': self.audit_notes,
            'archived': self.archived,
            'archive_path': self.archive_path,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

