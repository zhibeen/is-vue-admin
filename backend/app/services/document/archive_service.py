"""
自动归档服务
当报关单审核通过后，自动打包所有相关凭证进行归档
"""
from typing import List
from datetime import datetime
import os
import zipfile
from sqlalchemy import select
from app.models.document.document_center import DocumentCenter
from app.extensions import db
from app.errors import BusinessError


class ArchiveService:
    """归档服务类"""
    
    @staticmethod
    def archive_by_shipment(shipment_id: int, archived_by: int) -> str:
        """
        按发货单归档
        
        Args:
            shipment_id: 发货单ID
            archived_by: 归档操作人ID
            
        Returns:
            归档文件路径
        """
        # 获取该发货单的所有凭证
        stmt = select(DocumentCenter).where(
            DocumentCenter.business_type == 'logistics',
            DocumentCenter.business_id == shipment_id,
            DocumentCenter.archived == False,
            DocumentCenter.audit_status == 'approved'  # 只归档已审核通过的凭证
        )
        
        documents = db.session.execute(stmt).scalars().all()
        
        if not documents:
            raise BusinessError('没有可归档的凭证', code=400)
        
        # 生成归档文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_filename = f"shipment_{shipment_id}_{timestamp}.zip"
        archive_path = f"archives/logistics/{archive_filename}"
        
        # TODO: 实际项目中应该将文件打包并上传到OSS
        # 这里仅更新数据库状态
        
        # 更新归档状态
        for doc in documents:
            doc.archived = True
            doc.archive_path = archive_path
            doc.archived_at = datetime.now()
        
        db.session.commit()
        
        return archive_path
    
    @staticmethod
    def archive_by_customs_declaration(declaration_id: int, archived_by: int) -> str:
        """
        按报关单归档
        
        Args:
            declaration_id: 报关单ID
            archived_by: 归档操作人ID
            
        Returns:
            归档文件路径
            
        注意：
        - 报关单归档会同时归档关联发货单的凭证
        - 只归档已审核通过的凭证
        """
        # 获取报关单凭证
        stmt = select(DocumentCenter).where(
            DocumentCenter.business_type == 'customs',
            DocumentCenter.business_id == declaration_id,
            DocumentCenter.archived == False,
            DocumentCenter.audit_status == 'approved'
        )
        
        documents = db.session.execute(stmt).scalars().all()
        
        # TODO: 如果需要，可以同时归档关联发货单的凭证
        # 这需要查询报关单与发货单的关联关系
        
        if not documents:
            raise BusinessError('没有可归档的凭证', code=400)
        
        # 生成归档文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_filename = f"customs_{declaration_id}_{timestamp}.zip"
        archive_path = f"archives/customs/{archive_filename}"
        
        # 更新归档状态
        for doc in documents:
            doc.archived = True
            doc.archive_path = archive_path
            doc.archived_at = datetime.now()
        
        db.session.commit()
        
        return archive_path
    
    @staticmethod
    def archive_by_supplier(supplier_id: int, start_date: datetime, end_date: datetime, archived_by: int) -> str:
        """
        按供应商归档
        
        Args:
            supplier_id: 供应商ID
            start_date: 开始日期
            end_date: 结束日期
            archived_by: 归档操作人ID
            
        Returns:
            归档文件路径
        """
        # TODO: 实现按供应商归档逻辑
        # 需要查询供应商相关的采购单和凭证
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_filename = f"supplier_{supplier_id}_{timestamp}.zip"
        archive_path = f"archives/purchase/{archive_filename}"
        
        return archive_path
    
    @staticmethod
    def archive_by_month(year: int, month: int, archived_by: int) -> str:
        """
        按月度归档
        
        Args:
            year: 年份
            month: 月份
            archived_by: 归档操作人ID
            
        Returns:
            归档文件路径
        """
        # 计算月份的开始和结束日期
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        # 获取该月份的所有已审核凭证
        stmt = select(DocumentCenter).where(
            DocumentCenter.uploaded_at >= start_date,
            DocumentCenter.uploaded_at <= end_date,
            DocumentCenter.archived == False,
            DocumentCenter.audit_status == 'approved'
        )
        
        documents = db.session.execute(stmt).scalars().all()
        
        if not documents:
            raise BusinessError('该月份没有可归档的凭证', code=400)
        
        # 生成归档文件名
        archive_filename = f"monthly_{year}{month:02d}.zip"
        archive_path = f"archives/monthly/{archive_filename}"
        
        # 更新归档状态
        for doc in documents:
            doc.archived = True
            doc.archive_path = archive_path
            doc.archived_at = datetime.now()
        
        db.session.commit()
        
        return archive_path
    
    @staticmethod
    def get_archive_info(archive_path: str) -> dict:
        """
        获取归档信息
        
        Args:
            archive_path: 归档路径
            
        Returns:
            归档信息
        """
        # 查询使用此归档路径的凭证
        stmt = select(DocumentCenter).where(
            DocumentCenter.archive_path == archive_path
        )
        
        documents = db.session.execute(stmt).scalars().all()
        
        if not documents:
            return {
                'archive_path': archive_path,
                'document_count': 0,
                'archived_at': None,
                'documents': []
            }
        
        return {
            'archive_path': archive_path,
            'document_count': len(documents),
            'archived_at': documents[0].archived_at.isoformat() if documents[0].archived_at else None,
            'documents': [
                {
                    'id': doc.id,
                    'file_name': doc.file_name,
                    'business_type': doc.business_type,
                    'business_no': doc.business_no,
                }
                for doc in documents
            ]
        }

