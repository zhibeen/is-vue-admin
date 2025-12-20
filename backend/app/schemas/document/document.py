"""凭证管理Schema"""
from apiflask import Schema
from apiflask.fields import String, Integer, Boolean, DateTime
from marshmallow import validates, ValidationError


class DocumentCenterSchema(Schema):
    """凭证中心输出Schema"""
    id = Integer(dump_only=True)
    business_type = String(
        required=True,
        metadata={
            'description': '业务类型: logistics/purchase/customs/payment',
            'example': 'logistics'
        }
    )
    document_type = String(
        metadata={
            'description': '凭证类型',
            'example': 'logistics_voucher'
        }
    )
    document_category = String(
        metadata={
            'description': '文档分类: service_voucher/payment_voucher/contract_voucher/invoice_voucher/customs_voucher',
            'example': 'service_voucher'
        }
    )
    business_id = Integer(
        required=True,
        metadata={
            'description': '业务单据ID',
            'example': 1001
        }
    )
    business_no = String(
        metadata={
            'description': '业务单据编号',
            'example': 'SO202512190001'
        }
    )
    file_name = String(
        required=True,
        metadata={
            'description': '文件名',
            'example': 'invoice_20251219.pdf'
        }
    )
    file_path = String(
        dump_only=True,
        metadata={
            'description': '文件路径'
        }
    )
    file_size = Integer(
        dump_only=True,
        metadata={
            'description': '文件大小(bytes)',
            'example': 1024000
        }
    )
    file_type = String(
        dump_only=True,
        metadata={
            'description': '文件扩展名',
            'example': '.pdf'
        }
    )
    file_url = String(
        dump_only=True,
        metadata={
            'description': '可访问URL'
        }
    )
    uploaded_by_id = Integer(
        dump_only=True,
        metadata={
            'description': '上传人ID'
        }
    )
    uploaded_at = DateTime(
        dump_only=True,
        metadata={
            'description': '上传时间'
        }
    )
    audit_status = String(
        dump_only=True,
        metadata={
            'description': '审核状态: pending/approved/rejected',
            'example': 'pending'
        }
    )
    audited_by_id = Integer(
        dump_only=True,
        metadata={
            'description': '审核人ID'
        }
    )
    audited_at = DateTime(
        dump_only=True,
        metadata={
            'description': '审核时间'
        }
    )
    audit_notes = String(
        dump_only=True,
        metadata={
            'description': '审核备注'
        }
    )
    archived = Boolean(
        dump_only=True,
        metadata={
            'description': '是否已归档',
            'example': False
        }
    )
    archive_path = String(
        dump_only=True,
        metadata={
            'description': '归档路径'
        }
    )
    archived_at = DateTime(
        dump_only=True,
        metadata={
            'description': '归档时间'
        }
    )
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)


class DocumentUploadSchema(Schema):
    """凭证上传Schema"""
    business_type = String(
        required=True,
        metadata={
            'description': '业务类型: logistics/purchase/customs/payment',
            'example': 'logistics'
        }
    )
    business_id = Integer(
        required=True,
        metadata={
            'description': '业务单据ID',
            'example': 1001
        }
    )
    business_no = String(
        metadata={
            'description': '业务单据编号',
            'example': 'SO202512190001'
        }
    )
    document_type = String(
        metadata={
            'description': '凭证类型',
            'example': 'logistics_voucher'
        }
    )
    document_category = String(
        metadata={
            'description': '文档分类',
            'example': 'service_voucher'
        }
    )
    
    @validates('business_type')
    def validate_business_type(self, value):
        """验证业务类型"""
        valid_types = ['logistics', 'purchase', 'customs', 'payment']
        if value not in valid_types:
            raise ValidationError(f'业务类型必须是: {", ".join(valid_types)}')
        return value


class DocumentQuerySchema(Schema):
    """凭证查询Schema"""
    business_type = String(
        metadata={
            'description': '业务类型筛选',
            'example': 'logistics'
        }
    )
    business_id = Integer(
        metadata={
            'description': '业务单据ID筛选',
            'example': 1001
        }
    )
    audit_status = String(
        metadata={
            'description': '审核状态筛选: pending/approved/rejected',
            'example': 'pending'
        }
    )
    archived = Boolean(
        metadata={
            'description': '是否已归档筛选',
            'example': False
        }
    )


class DocumentAuditSchema(Schema):
    """凭证审核Schema"""
    audit_status = String(
        required=True,
        metadata={
            'description': '审核状态: approved/rejected',
            'example': 'approved'
        }
    )
    audit_notes = String(
        metadata={
            'description': '审核备注',
            'example': '凭证完整，审核通过'
        }
    )
    
    @validates('audit_status')
    def validate_audit_status(self, value):
        """验证审核状态"""
        valid_statuses = ['approved', 'rejected']
        if value not in valid_statuses:
            raise ValidationError(f'审核状态必须是: {", ".join(valid_statuses)}')
        return value

