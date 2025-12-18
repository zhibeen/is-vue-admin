from apiflask import Schema, abort
from apiflask.fields import Integer, String, Decimal, List, Boolean, Nested, Date, File
from apiflask.views import MethodView
from werkzeug.datastructures import FileStorage
from app.services.serc.tax_refund_service import tax_refund_service
from app.services.customs_service import customs_service
from app.schemas.pagination import PaginationQuerySchema, make_pagination_schema
from app.decorators import permission_required
from app.security import auth
import os
from . import customs_bp
from app.models.customs.consignee import OverseasConsignee
from app.models.customs.product import CustomsProduct
from app.extensions import db
from sqlalchemy import select

# --- Schemas ---

class OverseasConsigneeSchema(Schema):
    id = Integer(dump_only=True)
    name = String(required=True)
    address = String()
    contact_info = String()
    country = String()
    is_active = Boolean()

class CustomsProductSchema(Schema):
    id = Integer(dump_only=True)
    name = String(required=True)
    hs_code = String(required=True)
    rebate_rate = Decimal()
    unit = String()
    elements = String()
    description = String()
    is_active = Boolean()

class ContractSummarySchema(Schema):
    id = Integer()
    contract_no = String()
    supplier_id = Integer()
    supplier_name = String(attribute='supplier.name')
    total_amount = Decimal()
    status = String()

class CustomsDeclarationStatsSchema(Schema):
    status = String()
    count = Integer()
    label = String()

@customs_bp.route('/declarations/stats')
class DeclarationStatsAPI(MethodView):
    decorators = [customs_bp.auth_required(auth), permission_required('customs:view')]
    
    @customs_bp.doc(summary="获取报关单状态统计")
    @customs_bp.output(CustomsDeclarationStatsSchema(many=True))
    def get(self):
        return {'data': customs_service.get_declaration_stats()}

class CustomsDeclarationItemSchema(Schema):
    class Meta:
        unknown = 'EXCLUDE'

    supplier_id = Integer(dump_only=True)
    supplier_name = String(attribute='supplier.name', dump_only=True)
    sku = String(dump_only=True)
    
    # 基础信息
    item_no = Integer()
    hs_code = String()
    product_name_spec = String()
    
    # 数量1
    qty = Decimal(required=True)
    unit = String()

    # 数量1 (法定)
    qty_1 = Decimal(allow_none=True)
    unit_1 = String(allow_none=True)
    
    # 数量2
    qty_2 = Decimal(allow_none=True)
    unit_2 = String(allow_none=True)
    
    # 价格
    usd_unit_price = Decimal(required=True)
    usd_total = Decimal(required=True)
    currency = String()
    
    # 原产地与目的国
    origin_country = String()
    final_dest_country = String()
    district_code = String()
    exemption_way = String()
    
    # Packing Info
    box_no = String(dump_only=True)
    net_weight = Decimal(dump_only=True)
    gross_weight = Decimal(dump_only=True)

class CustomsDeclarationSchema(Schema):
    class Meta:
        unknown = 'EXCLUDE'  # 自动忽略前端传入的未知字段（如 dump_only 字段）

    id = Integer(dump_only=True)
    status = String(dump_only=True)
    
    # 基础信息
    pre_entry_no = String(dump_only=True)  # 自动生成，不允许手动设置
    customs_no = String()
    filing_no = String()
    internal_shipper_id = Integer()
    internal_shipper_name = String(attribute='internal_shipper.legal_name', dump_only=True)
    overseas_consignee = String()
    
    # 日期与备案
    export_date = Date()
    declare_date = Date()
    
    # 港口与地区
    departure_port = String()
    entry_port = String()
    destination_country = String()
    trade_country = String()
    loading_port = String()
    
    # 运输信息
    transport_mode = String()
    conveyance_ref = String()
    bill_of_lading_no = String()
    shipping_no = String(load_only=True) # Alias for input
    shipping_date = Date(allow_none=True)
    
    # 贸易信息
    trade_mode = String()
    nature_of_exemption = String()
    license_no = String()
    contract_no = String()
    transaction_mode = String()
    
    # 费用
    freight = Decimal(allow_none=True)
    insurance = Decimal(allow_none=True)
    incidental = Decimal(allow_none=True)
    
    # 包装与重量
    package_type = String()
    pack_count = Integer()
    gross_weight = Decimal()
    net_weight = Decimal()
    
    # 备注
    marks_and_notes = String()
    documents = String(allow_none=True)
    
    # 金额
    fob_total = Decimal()
    currency = String()
    exchange_rate = Decimal()
    
    # 统计
    product_count = Integer(dump_only=True)

    # 源数据
    source_type = String(dump_only=True)
    
    # 货柜模式
    container_mode = String()
    
    items = List(Nested(CustomsDeclarationItemSchema))
    contracts = List(Nested(ContractSummarySchema), dump_only=True)
    created_at = Date(dump_only=True)
    
    # 动态逻辑字段
    required_file_slots = List(String(), dump_only=True)

class DeclarationImportSchema(Schema):
    file = File(required=True)
    shipping_no = String(load_only=True)
    bill_of_lading_no = String(dump_only=True)
    logistics_provider = String()
    container_mode = String(load_only=True)
    export_date = Date()

class GenerateContractsResponseSchema(Schema):
    contract_ids = List(Integer())
    message = String()

class DeclarationQuerySchema(PaginationQuerySchema):
    status = String(metadata={'description': '状态筛选'})
    search_no = String(metadata={'description': '编号搜索（模糊搜索：预录入编号/报关单单号）'})
    pre_entry_no = String(metadata={'description': '预录入编号（精确搜索）'})
    container_mode = String(metadata={'description': '货柜模式：FCL/LCL'})

# --- Views ---

@customs_bp.route('/declarations')
class DeclarationListAPI(MethodView):
    @customs_bp.doc(summary="获取报关单列表", description="支持按预录入编号降序排序，search_no参数支持模糊搜索多字段")
    @customs_bp.input(DeclarationQuerySchema, location='query', arg_name='query')
    @customs_bp.output(make_pagination_schema(CustomsDeclarationSchema))
    def get(self, query):
        pagination = customs_service.get_declarations(
            query['page'],
            query['per_page'],
            filters={
                'status': query.get('status'), 
                'search_no': query.get('search_no'),
                'pre_entry_no': query.get('pre_entry_no'),
                'container_mode': query.get('container_mode')
            }
        )
        return {'data': pagination}

    @customs_bp.doc(summary="创建报关单 (草稿)")
    @customs_bp.input(CustomsDeclarationSchema, arg_name='data')
    @customs_bp.output(CustomsDeclarationSchema, status_code=201)
    @permission_required('customs:create')
    def post(self, data):
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
        return {'data': customs_service.create_declaration(data, current_user_id)}

@customs_bp.route('/declarations/import')
class DeclarationImportAPI(MethodView):
    decorators = [customs_bp.auth_required(auth)]
    
    @customs_bp.doc(summary="导入报关单/装箱单 (Excel)", description="上传Excel生成草稿报关单")
    @customs_bp.input(DeclarationImportSchema, location='form', arg_name='data')
    @customs_bp.output(CustomsDeclarationSchema, status_code=201)
    @permission_required('customs:create')
    def post(self, data):
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
        
        f: FileStorage = data['file']
        # Save temp file
        temp_path = f"/tmp/{f.filename}"
        if not os.path.exists('/tmp'):
            os.makedirs('/tmp')
        f.save(temp_path)
        
        try:
            source_data = {
                'shipping_no': data.get('shipping_no'),
                'logistics_provider': data.get('logistics_provider'),
                'container_mode': data.get('container_mode'),
                'export_date': data.get('export_date')
            }
            decl = customs_service.import_declaration_from_excel(temp_path, source_data, current_user_id)
            return {'data': decl}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

@customs_bp.route('/declarations/<int:id>/generate-contracts')
class DeclarationGenerateContractsAPI(MethodView):
    @customs_bp.doc(summary="生成交付合同", description="根据报关单明细按供应商拆分生成交付合同")
    @customs_bp.output(GenerateContractsResponseSchema)
    def post(self, id):
        contract_ids = customs_service.generate_contracts_from_declaration(id)
        return {'data': {
            'contract_ids': contract_ids, 
            'message': f'Successfully generated {len(contract_ids)} contracts'
        }}

@customs_bp.route('/declarations/<int:id>')
class DeclarationDetailAPI(MethodView):
    decorators = [customs_bp.auth_required(auth)]
    
    @customs_bp.doc(summary="获取报关单详情")
    @customs_bp.output(CustomsDeclarationSchema)
    @permission_required('customs:view')
    def get(self, id):
        return {'data': customs_service.get_declaration(id)}

    @customs_bp.doc(summary="更新报关单")
    @customs_bp.input(CustomsDeclarationSchema(partial=True), arg_name='data')
    @customs_bp.output(CustomsDeclarationSchema)
    @permission_required('customs:edit')
    def put(self, id, data):
        return {'data': customs_service.update_declaration(id, data)}

class StatusChangeSchema(Schema):
    """状态变更请求Schema"""
    status = String(required=True, metadata={'description': '新状态'})
    reason = String(metadata={'description': '变更原因（修撤时必填）'})

class DownloadPdfRequestSchema(Schema):
    """下载PDF请求Schema"""
    includes = List(String(), required=True, metadata={
        'description': '包含的内容类型',
        'example': ['declaration', 'packing', 'invoice']
    })

class PdfDownloadResponseSchema(Schema):
    """PDF下载响应Schema"""
    pdf_base64 = String(required=True, metadata={'description': 'PDF文件的Base64编码'})
    filename = String(required=True, metadata={'description': '文件名'})

@customs_bp.route('/declarations/<int:id>/download-pdf')
class DeclarationDownloadPdfAPI(MethodView):
    decorators = [customs_bp.auth_required(auth)]
    
    @customs_bp.doc(summary="下载报关单PDF", description="根据选择的内容生成PDF文件（返回Base64编码）")
    @customs_bp.input(DownloadPdfRequestSchema, arg_name='data')
    @customs_bp.output(PdfDownloadResponseSchema)
    @permission_required('customs:view')
    def post(self, id, data):
        """生成并下载报关单PDF"""
        import base64
        from app.services.customs.pdf_service import generate_declaration_pdf, generate_archived_files_pdf
        from flask_jwt_extended import get_jwt_identity
        from app.models.user import User
        
        # 获取报关单数据
        decl = customs_service.get_declaration(id)
        if not decl:
            abort(404, message="Declaration not found")
        
        # 获取当前下载用户
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id) if current_user_id else None
        
        # 判断是否为归档资料下载（仅包含 files，或 files + attachments）
        includes = data['includes']
        if includes == ['files'] or (set(includes) == {'files', 'attachments'}):
            # 归档资料：材料清单 + 所有附件PDF合并
            pdf_buffer = generate_archived_files_pdf(decl, current_user)
            filename_prefix = "归档资料"
        else:
            # 常规文档生成
            pdf_buffer = generate_declaration_pdf(decl, includes, current_user)
            filename_prefix = "报关单"
        
        # 读取PDF内容并转换为Base64
        pdf_bytes = pdf_buffer.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # 生成规范化文件名
        from datetime import datetime
        pre_entry_no = decl.pre_entry_no or decl.customs_no or f"DECL{decl.id}"
        date_str = ""
        if decl.declare_date:
            date_str = f"_{decl.declare_date.strftime('%Y%m%d')}"
        elif decl.export_date:
            date_str = f"_{decl.export_date.strftime('%Y%m%d')}"
        
        filename = f"{filename_prefix}_{pre_entry_no}{date_str}.pdf"
        
        return {
            'data': {
                'pdf_base64': pdf_base64,
                'filename': filename
            }
        }

@customs_bp.route('/declarations/<int:id>/status')
class DeclarationStatusAPI(MethodView):
    decorators = [customs_bp.auth_required(auth)]
    
    @customs_bp.doc(summary="变更报关单状态", description="带流转控制的状态变更")
    @customs_bp.input(StatusChangeSchema, arg_name='data')
    @customs_bp.output(CustomsDeclarationSchema)
    @permission_required('customs:approve')  # 状态变更需要审批权限
    def post(self, id, data):
        """变更报关单状态"""
        return {'data': customs_service.change_status(
            id,
            data['status'],
            data.get('reason')
        )}
    
    @customs_bp.doc(summary="获取允许的状态转换")
    @customs_bp.output(Schema.from_dict({
        'current_status': String(),
        'is_locked': Boolean(),
        'allowed_transitions': List(Nested(Schema.from_dict({
            'status': String(),
            'description': String()
        })))
    }))
    @permission_required('customs:view')
    def get(self, id):
        """获取允许的状态转换"""
        from app.services.customs.status_manager import DeclarationStatusManager
        
        decl = customs_service.get_declaration(id)
        if not decl:
            abort(404, message="Declaration not found")
        
        return {'data': {
            'current_status': decl.status,
            'is_locked': decl.is_locked,
            'allowed_transitions': DeclarationStatusManager.get_allowed_transitions(decl.status)
        }}

@customs_bp.route('/consignees')
class ConsigneeListAPI(MethodView):
    @customs_bp.doc(summary="获取境外收货人列表")
    @customs_bp.output(OverseasConsigneeSchema(many=True))
    def get(self):
        return {'data': db.session.scalars(select(OverseasConsignee).filter_by(is_active=True).order_by(OverseasConsignee.id)).all()}

    @customs_bp.doc(summary="创建境外收货人")
    @customs_bp.input(OverseasConsigneeSchema, arg_name='data')
    @customs_bp.output(OverseasConsigneeSchema, status_code=201)
    def post(self, data):
        consignee = OverseasConsignee(**data)
        db.session.add(consignee)
        db.session.commit()
        return {'data': consignee}

from app.schemas.pagination import PaginationQuerySchema, make_pagination_schema

# --- Customs Product Library API ---

@customs_bp.route('/products')
class CustomsProductListAPI(MethodView):
    @customs_bp.doc(summary="获取报关品类库")
    @customs_bp.input(PaginationQuerySchema, location='query', arg_name='pagination')
    @customs_bp.output(make_pagination_schema(CustomsProductSchema))
    def get(self, pagination):
        stmt = select(CustomsProduct).filter_by(is_active=True).order_by(CustomsProduct.name)
        pagination_data = db.paginate(stmt, page=pagination['page'], per_page=pagination['per_page'])
        return {
            'data': {
                'items': pagination_data.items,
                'total': pagination_data.total,
                'page': pagination_data.page,
                'per_page': pagination_data.per_page,
                'pages': pagination_data.pages
            }
        }

    @customs_bp.doc(summary="创建报关品类")
    @customs_bp.input(CustomsProductSchema, arg_name='data')
    @customs_bp.output(CustomsProductSchema, status_code=201)
    def post(self, data):
        prod = CustomsProduct(**data)
        db.session.add(prod)
        db.session.commit()
        return {'data': prod}

@customs_bp.route('/products/<int:id>')
class CustomsProductDetailAPI(MethodView):
    @customs_bp.doc(summary="更新报关品类")
    @customs_bp.input(CustomsProductSchema(partial=True), arg_name='data')
    @customs_bp.output(CustomsProductSchema)
    def put(self, id, data):
        prod = db.session.get(CustomsProduct, id)
        if not prod:
            abort(404, 'Product not found')
            
        for k, v in data.items():
            setattr(prod, k, v)
            
        db.session.commit()
        return {'data': prod}

    @customs_bp.doc(summary="删除报关品类")
    def delete(self, id):
        prod = db.session.get(CustomsProduct, id)
        if not prod:
            abort(404, 'Product not found')
            
        # 解除关联: 将所有引用该品类的 SKU 的 customs_product_id 设为 NULL
        from app.models.product.item import ProductVariant
        db.session.query(ProductVariant).filter(ProductVariant.customs_product_id == id).update({ProductVariant.customs_product_id: None})
        
        db.session.delete(prod)
        db.session.commit()
        return {'code': 0, 'message': 'success', 'data': None}

@customs_bp.route('/consignees/<int:id>')
class ConsigneeDetailAPI(MethodView):
    @customs_bp.doc(summary="更新境外收货人")
    @customs_bp.input(OverseasConsigneeSchema(partial=True), arg_name='data')
    @customs_bp.output(OverseasConsigneeSchema)
    def put(self, id, data):
        consignee = db.session.get(OverseasConsignee, id)
        if not consignee:
            abort(404, 'Consignee not found')
            
        for k, v in data.items():
            setattr(consignee, k, v)
            
        db.session.commit()
        return {'data': consignee}
