"""
凭证管理服务层
处理凭证上传、查询、审核、归档等业务逻辑
"""
from typing import List, Optional
from datetime import datetime
import os
from sqlalchemy import select
from werkzeug.utils import secure_filename
from app.models.document.document_center import DocumentCenter, BusinessType, AuditStatus
from app.extensions import db
from app.errors import BusinessError


class DocumentService:
    """凭证管理业务逻辑类"""
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.doc', '.docx'}
    
    # 最大文件大小（10MB）
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @staticmethod
    def validate_file(file) -> tuple[bool, str]:
        """
        验证文件
        
        Args:
            file: 上传的文件对象
            
        Returns:
            (是否有效, 错误消息)
        """
        if not file:
            return False, '文件不能为空'
        
        if not file.filename:
            return False, '文件名不能为空'
        
        # 检查文件扩展名
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in DocumentService.ALLOWED_EXTENSIONS:
            return False, f'不支持的文件类型: {file_ext}'
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > DocumentService.MAX_FILE_SIZE:
            return False, f'文件大小超过限制({DocumentService.MAX_FILE_SIZE / 1024 / 1024}MB)'
        
        return True, ''
    
    @staticmethod
    def upload_document(
        business_type: str,
        business_id: int,
        file,
        metadata: dict,
        uploaded_by: int
    ) -> DocumentCenter:
        """
        上传凭证
        
        Args:
            business_type: 业务类型(logistics/purchase/customs/payment)
            business_id: 业务单据ID
            file: 文件对象
            metadata: 元数据(document_type, document_category, business_no等)
            uploaded_by: 上传人ID
            
        Returns:
            创建的凭证对象
            
        Raises:
            BusinessError: 文件验证失败时
        """
        # 验证文件
        is_valid, error_msg = DocumentService.validate_file(file)
        if not is_valid:
            raise BusinessError(error_msg, code=400)
        
        # 获取安全的文件名
        original_filename = secure_filename(file.filename)
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        # 生成文件路径（实际项目中应保存到OSS/NAS）
        # 格式: uploads/{business_type}/{business_id}/{timestamp}_{filename}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{timestamp}_{original_filename}"
        file_path = f"uploads/{business_type}/{business_id}/{file_name}"
        
        # TODO: 实际项目中应保存文件到文件系统或OSS
        # file.save(file_path)
        # 或 upload_to_oss(file, file_path)
        
        # 获取文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        # 创建凭证记录
        document = DocumentCenter(
            business_type=business_type,
            business_id=business_id,
            document_type=metadata.get('document_type'),
            document_category=metadata.get('document_category'),
            business_no=metadata.get('business_no'),
            file_name=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_ext,
            file_url=None,  # TODO: 生成预签名URL
            uploaded_by_id=uploaded_by,
            uploaded_at=datetime.now(),
            audit_status=AuditStatus.PENDING.value
        )
        
        db.session.add(document)
        db.session.commit()
        db.session.refresh(document)
        
        return document
    
    @staticmethod
    def get_documents_by_business(
        business_type: str,
        business_id: int
    ) -> List[DocumentCenter]:
        """
        按业务单据查询凭证
        
        Args:
            business_type: 业务类型
            business_id: 业务单据ID
            
        Returns:
            凭证列表
        """
        stmt = select(DocumentCenter).where(
            DocumentCenter.business_type == business_type,
            DocumentCenter.business_id == business_id
        ).order_by(DocumentCenter.uploaded_at.desc())
        
        return db.session.execute(stmt).scalars().all()
    
    @staticmethod
    def get_document_by_id(document_id: int) -> Optional[DocumentCenter]:
        """
        根据ID获取凭证
        
        Args:
            document_id: 凭证ID
            
        Returns:
            凭证对象或None
        """
        return db.session.get(DocumentCenter, document_id)
    
    @staticmethod
    def query_documents(
        business_type: Optional[str] = None,
        audit_status: Optional[str] = None,
        archived: Optional[bool] = None,
        uploaded_by_id: Optional[int] = None
    ) -> List[DocumentCenter]:
        """
        查询凭证（支持多条件筛选）
        
        Args:
            business_type: 业务类型筛选
            audit_status: 审核状态筛选
            archived: 是否已归档筛选
            uploaded_by_id: 上传人筛选
            
        Returns:
            凭证列表
        """
        stmt = select(DocumentCenter)
        
        # 筛选条件
        if business_type:
            stmt = stmt.where(DocumentCenter.business_type == business_type)
        if audit_status:
            stmt = stmt.where(DocumentCenter.audit_status == audit_status)
        if archived is not None:
            stmt = stmt.where(DocumentCenter.archived == archived)
        if uploaded_by_id:
            stmt = stmt.where(DocumentCenter.uploaded_by_id == uploaded_by_id)
        
        # 排序
        stmt = stmt.order_by(DocumentCenter.uploaded_at.desc())
        
        return db.session.execute(stmt).scalars().all()
    
    @staticmethod
    def audit_document(
        document_id: int,
        audited_by: int,
        status: str,
        notes: Optional[str] = None
    ) -> DocumentCenter:
        """
        审核凭证
        
        Args:
            document_id: 凭证ID
            audited_by: 审核人ID
            status: 审核状态(approved/rejected)
            notes: 审核备注
            
        Returns:
            更新后的凭证对象
            
        Raises:
            BusinessError: 凭证不存在或状态无效时
        """
        document = DocumentService.get_document_by_id(document_id)
        if not document:
            raise BusinessError('凭证不存在', code=404)
        
        if status not in [AuditStatus.APPROVED.value, AuditStatus.REJECTED.value]:
            raise BusinessError('无效的审核状态', code=400)
        
        document.audit_status = status
        document.audited_by_id = audited_by
        document.audited_at = datetime.now()
        document.audit_notes = notes
        
        db.session.commit()
        db.session.refresh(document)
        
        return document
    
    @staticmethod
    def delete_document(document_id: int) -> None:
        """
        删除凭证
        
        Args:
            document_id: 凭证ID
            
        Raises:
            BusinessError: 凭证不存在或已归档时
        """
        document = DocumentService.get_document_by_id(document_id)
        if not document:
            raise BusinessError('凭证不存在', code=404)
        
        if document.archived:
            raise BusinessError('已归档的凭证不能删除', code=400)
        
        # TODO: 删除实际文件
        # delete_file(document.file_path)
        
        db.session.delete(document)
        db.session.commit()
    
    @staticmethod
    def archive_documents(document_ids: List[int], archive_path: str) -> int:
        """
        批量归档凭证
        
        Args:
            document_ids: 凭证ID列表
            archive_path: 归档路径
            
        Returns:
            归档的凭证数量
        """
        stmt = select(DocumentCenter).where(
            DocumentCenter.id.in_(document_ids),
            DocumentCenter.archived == False
        )
        
        documents = db.session.execute(stmt).scalars().all()
        
        for doc in documents:
            doc.archived = True
            doc.archive_path = archive_path
            doc.archived_at = datetime.now()
        
        db.session.commit()
        
        return len(documents)

