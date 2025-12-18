"""
报关单审计日志模型
"""
from sqlalchemy import String, Integer, ForeignKey, DateTime, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db


class CustomsDeclarationAuditLog(db.Model):
    """
    报关单审计日志
    记录所有重要操作和数据变更
    """
    __tablename__ = "customs_declaration_audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 关联信息
    declaration_id: Mapped[int] = mapped_column(
        ForeignKey("customs_declarations.id"),
        comment='报关单ID'
    )
    
    # 操作信息
    action: Mapped[str] = mapped_column(
        String(50),
        comment='操作类型: create/update/delete/status_change/file_upload'
    )
    action_description: Mapped[str] = mapped_column(
        String(255),
        comment='操作描述'
    )
    
    # 数据变更（存储为JSON）
    old_value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True,
        comment='变更前的值'
    )
    new_value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True,
        comment='变更后的值'
    )
    
    # 变更摘要（便于查询）
    changes_summary: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='变更摘要'
    )
    
    # 操作人信息
    operator_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        comment='操作人ID'
    )
    operator_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment='操作人姓名'
    )
    
    # 请求信息
    ip_address: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        comment='IP地址'
    )
    user_agent: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment='用户代理'
    )
    
    # 时间戳
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment='创建时间'
    )
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} by {self.operator_name}>"

