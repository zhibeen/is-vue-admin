"""凭证管理API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from flask import request
from flask_jwt_extended import get_jwt_identity
from app.security import auth
from app.decorators import permission_required
from app.schemas.document import (
    DocumentCenterSchema,
    DocumentUploadSchema,
    DocumentQuerySchema,
    DocumentAuditSchema
)
from app.services.document import DocumentService, ArchiveService


document_bp = APIBlueprint(
    'documents', 
    __name__, 
    url_prefix='/documents', 
    tag='凭证管理'
)


class DocumentUploadAPI(MethodView):
    """凭证上传API"""
    decorators = [document_bp.auth_required(auth)]
    
    @document_bp.doc(
        summary='上传凭证',
        description='上传业务凭证文件（支持PDF、图片、Excel等格式）'
    )
    @document_bp.output(DocumentCenterSchema, status_code=201)
    def post(self):
        """上传凭证"""
        user_id = get_jwt_identity()
        
        # 获取表单参数
        business_type = request.form.get('business_type')
        business_id = request.form.get('business_id')
        business_no = request.form.get('business_no')
        document_type = request.form.get('document_type')
        document_category = request.form.get('document_category')
        
        # 验证必填参数
        if not business_type or not business_id:
            return {'error': 'business_type和business_id为必填项'}, 400
        
        # 获取文件
        file = request.files.get('file')
        if not file:
            return {'error': '请选择要上传的文件'}, 400
        
        # 上传凭证
        document = DocumentService.upload_document(
            business_type=business_type,
            business_id=int(business_id),
            file=file,
            metadata={
                'document_type': document_type,
                'document_category': document_category,
                'business_no': business_no
            },
            uploaded_by=user_id
        )
        
        return {'data': document}


class DocumentListAPI(MethodView):
    """凭证列表API"""
    decorators = [document_bp.auth_required(auth)]
    
    @document_bp.doc(
        summary='查询凭证列表',
        description='查询凭证列表，支持按业务类型、业务单据ID、审核状态等筛选'
    )
    @document_bp.input(DocumentQuerySchema, location='query', arg_name='query')
    @document_bp.output(DocumentCenterSchema(many=True))
    def get(self, query):
        """查询凭证列表"""
        # 如果指定了business_type和business_id，使用专门的查询方法
        if query.get('business_type') and query.get('business_id'):
            documents = DocumentService.get_documents_by_business(
                business_type=query['business_type'],
                business_id=query['business_id']
            )
        else:
            # 否则使用通用查询方法
            documents = DocumentService.query_documents(
                business_type=query.get('business_type'),
                audit_status=query.get('audit_status'),
                archived=query.get('archived')
            )
        
        return {'data': documents}


class DocumentItemAPI(MethodView):
    """凭证详情API"""
    decorators = [document_bp.auth_required(auth)]
    
    @document_bp.doc(
        summary='获取凭证详情',
        description='根据ID获取凭证详细信息'
    )
    @document_bp.output(DocumentCenterSchema)
    def get(self, document_id: int):
        """获取凭证详情"""
        document = DocumentService.get_document_by_id(document_id)
        if not document:
            return {'error': '凭证不存在'}, 404
        return {'data': document}
    
    @document_bp.doc(
        summary='删除凭证',
        description='删除凭证记录及文件'
    )
    @document_bp.output({}, status_code=204)
    @permission_required('document:delete')
    def delete(self, document_id: int):
        """删除凭证"""
        DocumentService.delete_document(document_id)
        return None


class DocumentAuditAPI(MethodView):
    """凭证审核API"""
    decorators = [document_bp.auth_required(auth)]
    
    @document_bp.doc(
        summary='审核凭证',
        description='审核凭证，设置为通过或驳回'
    )
    @document_bp.input(DocumentAuditSchema, arg_name='data')
    @document_bp.output(DocumentCenterSchema)
    @permission_required('document:audit')
    def post(self, document_id: int, data):
        """审核凭证"""
        user_id = get_jwt_identity()
        
        document = DocumentService.audit_document(
            document_id=document_id,
            audited_by=user_id,
            status=data['audit_status'],
            notes=data.get('audit_notes')
        )
        
        return {'data': document}


class DocumentArchiveAPI(MethodView):
    """凭证归档API"""
    decorators = [document_bp.auth_required(auth)]
    
    @document_bp.doc(
        summary='归档凭证',
        description='按业务单据归档凭证'
    )
    @permission_required('document:archive')
    def post(self):
        """触发归档"""
        user_id = get_jwt_identity()
        data = request.json or {}
        
        archive_type = data.get('archive_type')  # shipment/customs/supplier/month
        archive_id = data.get('archive_id')
        
        if archive_type == 'shipment':
            archive_path = ArchiveService.archive_by_shipment(archive_id, user_id)
        elif archive_type == 'customs':
            archive_path = ArchiveService.archive_by_customs_declaration(archive_id, user_id)
        elif archive_type == 'month':
            year = data.get('year')
            month = data.get('month')
            archive_path = ArchiveService.archive_by_month(year, month, user_id)
        else:
            return {'error': '不支持的归档类型'}, 400
        
        return {'data': {'archive_path': archive_path}}


# 注册路由
document_bp.add_url_rule(
    '/upload',
    view_func=DocumentUploadAPI.as_view('upload'),
    methods=['POST']
)

document_bp.add_url_rule(
    '',
    view_func=DocumentListAPI.as_view('list'),
    methods=['GET']
)

document_bp.add_url_rule(
    '/<int:document_id>',
    view_func=DocumentItemAPI.as_view('item'),
    methods=['GET', 'DELETE']
)

document_bp.add_url_rule(
    '/<int:document_id>/audit',
    view_func=DocumentAuditAPI.as_view('audit'),
    methods=['POST']
)

document_bp.add_url_rule(
    '/archive',
    view_func=DocumentArchiveAPI.as_view('archive'),
    methods=['POST']
)

