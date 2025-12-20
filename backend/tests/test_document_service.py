"""
凭证管理模块测试
测试凭证上传、查询、审核等操作
"""
import pytest
from io import BytesIO
from app.models.document import DocumentCenter, AuditStatus
from app.services.document import DocumentService
from app.errors import BusinessError


class MockFile:
    """模拟文件对象"""
    def __init__(self, filename, content=b'test content', mimetype='application/pdf'):
        self.filename = filename
        self.content = content
        self.mimetype = mimetype
        self._position = 0
    
    def read(self, size=-1):
        if size == -1:
            result = self.content[self._position:]
            self._position = len(self.content)
        else:
            result = self.content[self._position:self._position + size]
            self._position += size
        return result
    
    def seek(self, position, whence=0):
        if whence == 0:  # SEEK_SET
            self._position = position
        elif whence == 1:  # SEEK_CUR
            self._position += position
        elif whence == 2:  # SEEK_END
            self._position = len(self.content) + position
    
    def tell(self):
        return self._position


class TestDocumentService:
    """凭证管理测试类"""
    
    def test_validate_file_success(self, app, db_session):
        """测试文件验证成功"""
        file = MockFile('test.pdf', content=b'x' * 1000, mimetype='application/pdf')
        is_valid, error_msg = DocumentService.validate_file(file)
        
        assert is_valid is True
        assert error_msg == ''
    
    def test_validate_file_empty(self, app, db_session):
        """测试空文件"""
        is_valid, error_msg = DocumentService.validate_file(None)
        
        assert is_valid is False
        assert '文件不能为空' in error_msg
    
    def test_validate_file_too_large(self, app, db_session):
        """测试文件过大"""
        # 创建11MB的文件
        large_content = b'x' * (11 * 1024 * 1024)
        file = MockFile('large.pdf', content=large_content)
        
        is_valid, error_msg = DocumentService.validate_file(file)
        
        assert is_valid is False
        assert '文件大小超过限制' in error_msg
    
    def test_upload_document(self, app, db_session):
        """测试上传凭证"""
        file = MockFile('invoice.pdf', content=b'test invoice content')
        
        metadata = {
            'document_type': 'invoice',
            'document_category': 'invoice_voucher',
            'business_no': 'SO202512190001'
        }
        
        document = DocumentService.upload_document(
            business_type='logistics',
            business_id=1,
            file=file,
            metadata=metadata,
            uploaded_by=1
        )
        
        assert document.id is not None
        assert document.business_type == 'logistics'
        assert document.business_id == 1
        assert document.file_name == 'invoice.pdf'
        assert document.audit_status == AuditStatus.PENDING.value
    
    def test_get_documents_by_business(self, app, db_session):
        """测试按业务单据查询凭证"""
        # 创建多个凭证
        for i in range(3):
            file = MockFile(f'doc{i}.pdf')
            DocumentService.upload_document(
                business_type='logistics',
                business_id=1,
                file=file,
                metadata={'document_type': 'test'},
                uploaded_by=1
            )
        
        # 创建其他业务的凭证
        file = MockFile('other.pdf')
        DocumentService.upload_document(
            business_type='logistics',
            business_id=2,
            file=file,
            metadata={'document_type': 'test'},
            uploaded_by=1
        )
        
        # 查询business_id=1的凭证
        documents = DocumentService.get_documents_by_business('logistics', 1)
        
        assert len(documents) == 3
        assert all(d.business_id == 1 for d in documents)
    
    def test_audit_document_approve(self, app, db_session):
        """测试审核通过凭证"""
        # 创建凭证
        file = MockFile('test.pdf')
        document = DocumentService.upload_document(
            business_type='logistics',
            business_id=1,
            file=file,
            metadata={'document_type': 'test'},
            uploaded_by=1
        )
        
        # 审核通过
        audited = DocumentService.audit_document(
            document_id=document.id,
            audited_by=1,
            status='approved',
            notes='审核通过'
        )
        
        assert audited.audit_status == 'approved'
        assert audited.audited_by_id == 1
        assert audited.audited_at is not None
        assert audited.audit_notes == '审核通过'
    
    def test_audit_document_reject(self, app, db_session):
        """测试驳回凭证"""
        file = MockFile('test.pdf')
        document = DocumentService.upload_document(
            business_type='logistics',
            business_id=1,
            file=file,
            metadata={'document_type': 'test'},
            uploaded_by=1
        )
        
        # 驳回
        audited = DocumentService.audit_document(
            document_id=document.id,
            audited_by=1,
            status='rejected',
            notes='凭证不清晰，请重新上传'
        )
        
        assert audited.audit_status == 'rejected'
        assert audited.audit_notes == '凭证不清晰，请重新上传'
    
    def test_delete_document(self, app, db_session):
        """测试删除凭证"""
        file = MockFile('test.pdf')
        document = DocumentService.upload_document(
            business_type='logistics',
            business_id=1,
            file=file,
            metadata={'document_type': 'test'},
            uploaded_by=1
        )
        document_id = document.id
        
        # 删除凭证
        DocumentService.delete_document(document_id)
        
        # 验证已删除
        found = DocumentService.get_document_by_id(document_id)
        assert found is None
    
    def test_delete_archived_document_should_fail(self, app, db_session):
        """测试删除已归档的凭证应失败"""
        file = MockFile('test.pdf')
        document = DocumentService.upload_document(
            business_type='logistics',
            business_id=1,
            file=file,
            metadata={'document_type': 'test'},
            uploaded_by=1
        )
        
        # 标记为已归档
        document.archived = True
        db_session.commit()
        
        # 尝试删除应失败
        with pytest.raises(BusinessError) as exc_info:
            DocumentService.delete_document(document.id)
        
        assert '已归档' in str(exc_info.value)
    
    def test_query_documents_with_filters(self, app, db_session):
        """测试带筛选条件查询凭证"""
        # 创建不同状态的凭证
        for i in range(2):
            file = MockFile(f'pending{i}.pdf')
            DocumentService.upload_document(
                business_type='logistics',
                business_id=1,
                file=file,
                metadata={'document_type': 'test'},
                uploaded_by=1
            )
        
        file = MockFile('approved.pdf')
        doc = DocumentService.upload_document(
            business_type='purchase',
            business_id=1,
            file=file,
            metadata={'document_type': 'test'},
            uploaded_by=1
        )
        DocumentService.audit_document(doc.id, 1, 'approved')
        
        # 查询logistics类型的待审核凭证
        pending_docs = DocumentService.query_documents(
            business_type='logistics',
            audit_status='pending'
        )
        
        assert len(pending_docs) >= 2
        assert all(d.audit_status == 'pending' for d in pending_docs)
        
        # 查询已审核的凭证
        approved_docs = DocumentService.query_documents(audit_status='approved')
        
        assert len(approved_docs) >= 1
        assert all(d.audit_status == 'approved' for d in approved_docs)
    
    def test_archive_documents(self, app, db_session):
        """测试批量归档凭证"""
        # 创建并审核多个凭证
        doc_ids = []
        for i in range(3):
            file = MockFile(f'doc{i}.pdf')
            doc = DocumentService.upload_document(
                business_type='logistics',
                business_id=1,
                file=file,
                metadata={'document_type': 'test'},
                uploaded_by=1
            )
            DocumentService.audit_document(doc.id, 1, 'approved')
            doc_ids.append(doc.id)
        
        # 归档
        archive_path = 'archives/test_archive.zip'
        count = DocumentService.archive_documents(doc_ids, archive_path)
        
        assert count == 3
        
        # 验证已归档
        for doc_id in doc_ids:
            doc = DocumentService.get_document_by_id(doc_id)
            assert doc.archived is True
            assert doc.archive_path == archive_path

