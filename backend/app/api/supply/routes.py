from apiflask.views import MethodView
from apiflask import HTTPError
from flask import send_file
from io import BytesIO
import zipfile
from app.schemas.serc.supply import (
    DeliveryContractCreateSchema, 
    DeliveryContractDetailSchema, 
    DeliveryContractSearchSchema,
    DeliveryContractPaginationSchema
)
from app.services.serc.supply_service import supply_service
from app.services.serc.pdf_service import pdf_service
from app.services.serc.excel_service import excel_service
from app.models.supply import ScmDeliveryContract, ScmDeliveryContractItem
from app.models.purchase.supplier import SysSupplier
from app.extensions import db
from . import supply_bp

from datetime import datetime

class DeliveryContractListAPI(MethodView):
    
    @supply_bp.input(DeliveryContractSearchSchema, location='query')
    @supply_bp.output(DeliveryContractPaginationSchema)
    def get(self, query_data):
        """获取 L1 交付合同列表"""
        pagination = supply_service.get_contract_list(
            page=query_data.get('page'),
            per_page=query_data.get('per_page'),
            filters=query_data
        )
        
        return {
            'data': {
                'items': pagination.items,
                'total': pagination.total,
                'pages': pagination.pages,
                'page': pagination.page,
                'per_page': pagination.per_page
            }
        }

    @supply_bp.input(DeliveryContractCreateSchema, arg_name='data')
    @supply_bp.output(DeliveryContractDetailSchema, status_code=201)
    def post(self, data):
        """手工创建 L1 交付合同"""
        # 本阶段跳过 Auth，直接调用 Service
        contract = supply_service.create_manual_contract(data)
        return {'data': contract}

@supply_bp.post('/contracts/print')
def print_contracts():
    """
    批量打印合同
    Payload: { "ids": [1, 2, 3] }
    """
    from flask import request
    data = request.get_json()
    ids = data.get('ids', [])
    if not ids:
        raise HTTPError(400, message='No IDs provided')

    # 1. 查询合同数据并按供应商分组
    contracts = db.session.query(ScmDeliveryContract).options(
        db.joinedload(ScmDeliveryContract.supplier),
        db.joinedload(ScmDeliveryContract.company),
        db.selectinload(ScmDeliveryContract.items).joinedload(ScmDeliveryContractItem.product),
        db.joinedload(ScmDeliveryContract.source_doc)
    ).filter(ScmDeliveryContract.id.in_(ids)).all()
    
    if not contracts:
         raise HTTPError(404, message='No contracts found')

    grouped = {}
    for c in contracts:
        s_name = c.supplier.name
        # 获取采购主体简称或名称，如果为空则显示"未指定主体"
        comp_name = c.company.short_name if c.company and c.company.short_name else (c.company.legal_name if c.company else "未指定主体")
        
        # 组合键
        key = (comp_name, s_name)
        
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(c)

    # 获取当前日期字符串，用于文件名
    date_str = datetime.now().strftime('%Y%m%d')

    # 2. 生成 PDF 服务
    if len(grouped) == 1:
        (comp_name, s_name) = list(grouped.keys())[0]
        c_list = grouped[(comp_name, s_name)]
        filename = f'{comp_name}_{s_name}_采购合同_{date_str}_{len(c_list)}份.pdf'
        
        pdf_bytes = pdf_service.generate_supplier_contract_pdf(s_name, c_list)
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    # 3. 多组数据，打包 ZIP
    memory_file = BytesIO()
    zip_filename = f'批量采购合同_{date_str}_共{len(contracts)}份.zip'
    
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for (comp_name, s_name), c_list in grouped.items():
            pdf_bytes = pdf_service.generate_supplier_contract_pdf(s_name, c_list)
            inner_filename = f'{comp_name}_{s_name}_采购合同_{date_str}_{len(c_list)}份.pdf'
            zf.writestr(inner_filename, pdf_bytes)
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@supply_bp.post('/contracts/export')
def export_contracts():
    """
    导出合同 Excel
    Payload: { "ids": [1, 2], "q": "...", "company_id": 1, ... }
    """
    from flask import request
    data = request.get_json() or {}
    
    ids = data.get('ids', [])
    
    # Base query with eager loading
    query = db.session.query(ScmDeliveryContract).options(
        db.joinedload(ScmDeliveryContract.supplier).joinedload(SysSupplier.payment_term),
        db.joinedload(ScmDeliveryContract.company),
        db.joinedload(ScmDeliveryContract.payment_term), 
        db.selectinload(ScmDeliveryContract.items).joinedload(ScmDeliveryContractItem.product),
        db.joinedload(ScmDeliveryContract.source_doc)
    )
    
    if ids:
        query = query.filter(ScmDeliveryContract.id.in_(ids))
    else:
        # Apply filters if no specific IDs provided (Export All based on search)
        if data.get('q'):
            keyword = f"%{data['q']}%"
            query = query.join(ScmDeliveryContract.supplier).filter(
                db.or_(
                    ScmDeliveryContract.contract_no.ilike(keyword),
                    SysSupplier.name.ilike(keyword)
                )
            )
        
        if data.get('supplier_id'):
            query = query.filter(ScmDeliveryContract.supplier_id == data['supplier_id'])
            
        if data.get('company_id'):
            query = query.filter(ScmDeliveryContract.company_id == data['company_id'])
            
        if data.get('status'):
            query = query.filter(ScmDeliveryContract.status == data['status'])

    contracts = query.all()
    
    if not contracts:
        raise HTTPError(404, message='No contracts found to export')

    excel_file = excel_service.generate_contracts_excel(contracts)
    
    filename = f'采购合同报表_{datetime.now().strftime("%Y%m%d%H%M")}.xlsx'
    
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# 注册路由
supply_bp.add_url_rule('/contracts', view_func=DeliveryContractListAPI.as_view('contract_list'))
