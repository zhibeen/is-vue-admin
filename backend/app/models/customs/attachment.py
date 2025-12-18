from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

if TYPE_CHECKING:
    from app.models.customs.declaration import CustomsDeclaration
    from app.models.user import User

class CustomsAttachment(db.Model):
    """
    报关单附件表
    记录文件元数据及NAS存储路径，作为文件系统的索引
    """
    __tablename__ = "customs_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    declaration_id: Mapped[int] = mapped_column(ForeignKey("customs_declarations.id"), index=True)
    
    # 文件物理信息
    file_name: Mapped[str] = mapped_column(String(255), comment="显示文件名")
    file_path: Mapped[str] = mapped_column(String(500), comment="NAS相对路径(含文件名)")
    file_size: Mapped[Optional[int]] = mapped_column(Integer, comment="文件大小(Bytes)")
    file_type: Mapped[Optional[str]] = mapped_column(String(50), comment="文件扩展名")
    
    # 业务分类
    category: Mapped[str] = mapped_column(String(50), default="04_Others", comment="目录分类")
    # slot_title 用于固定插槽（如：必须上传'报关单'），方便前端判断某个核心单据是否已上传
    slot_title: Mapped[Optional[str]] = mapped_column(String(100), comment="业务插槽标识")
    
    # 审计
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), comment="上传人ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # 同步状态
    status: Mapped[str] = mapped_column(String(20), default='synced', server_default='synced', comment='状态: synced/missing')
    source: Mapped[str] = mapped_column(String(20), default='upload', server_default='upload', comment='来源: upload/nas_sync')
    sync_message: Mapped[Optional[str]] = mapped_column(String(255), comment='同步异常备注')
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), comment='最后同步时间')

    # Relationships
    declaration: Mapped["CustomsDeclaration"] = relationship("CustomsDeclaration", back_populates="attachments")
    uploader: Mapped["User"] = relationship("User")

