"""发货单相关API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import or_

from app.security import auth
from app.decorators import permission_required
from app.schemas.logistics.shipment import (
    ShipmentOrderSchema,
    ShipmentOrderCreateSchema,
    ShipmentOrderUpdateSchema
)
from app.schemas.pagination import PaginationQuerySchema, PaginationSchema, make_pagination_schema
from app.services.logistics.shipment_service import ShipmentService
from app.models.logistics.shipment import ShipmentOrder
from app.extensions import db

logistics_bp = APIBlueprint('logistics', __name__, url_prefix='/logistics', tag='物流管理')


class ShipmentOrderListAPI(MethodView):
    """发货单列表API"""
    decorators = [logistics_bp.auth_required(auth)]
    
    @logistics_bp.doc(summary='获取发货单列表', description='支持分页、搜索、状态过滤')
    @logistics_bp.input(PaginationQuerySchema, location='query', arg_name='pagination')
    @logistics_bp.output(make_pagination_schema(ShipmentOrderSchema))
    def get(self, pagination):
        """获取发货单列表"""
        page = pagination['page']
        per_page = pagination['per_page']
        
        query = ShipmentOrder.query
        
        # 搜索过滤（发货单号、外部订单号、收货人）
        if pagination.get('q'):
            q = f"%{pagination['q']}%"
            query = query.filter(
                or_(
                    ShipmentOrder.shipment_no.ilike(q),
                    ShipmentOrder.external_order_no.ilike(q),
                    ShipmentOrder.consignee_name.ilike(q),
                    ShipmentOrder.tracking_no.ilike(q)
                )
            )
        
        # 状态过滤
        if pagination.get('status'):
            query = query.filter(ShipmentOrder.status == pagination['status'])
        
        # 来源过滤
        if pagination.get('source'):
            query = query.filter(ShipmentOrder.source == pagination['source'])
        
        # 日期范围过滤
        if pagination.get('start_date'):
            query = query.filter(ShipmentOrder.created_at >= pagination['start_date'])
        if pagination.get('end_date'):
            query = query.filter(ShipmentOrder.created_at <= pagination['end_date'])
        
        # 排序
        query = query.order_by(ShipmentOrder.created_at.desc())
        
        # 分页
        pagination_obj = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'data': {
                'items': pagination_obj.items,
                'total': pagination_obj.total,
                'page': page,
                'per_page': per_page
            }
        }
    
    @logistics_bp.doc(summary='创建发货单', description='创建新的发货单')
    @logistics_bp.input(ShipmentOrderCreateSchema, arg_name='data')
    @logistics_bp.output(ShipmentOrderSchema, status_code=201)
    @permission_required('logistics:shipment:create')
    def post(self, data):
        """创建发货单"""
        user_id = get_jwt_identity()
        shipment = ShipmentService.create_shipment(data, created_by=user_id)
        return {'data': shipment}


class ShipmentOrderItemAPI(MethodView):
    """发货单详情API"""
    decorators = [logistics_bp.auth_required(auth)]
    
    @logistics_bp.doc(summary='获取发货单详情', description='根据ID获取发货单详细信息')
    @logistics_bp.output(ShipmentOrderSchema)
    def get(self, shipment_id):
        """获取发货单详情"""
        from app.errors import BusinessError
        shipment = ShipmentService.get_shipment_by_id(shipment_id)
        if not shipment:
            raise BusinessError('发货单不存在', code=404)
        return {'data': shipment}
    
    @logistics_bp.doc(summary='更新发货单', description='更新发货单信息')
    @logistics_bp.input(ShipmentOrderUpdateSchema, arg_name='data')
    @logistics_bp.output(ShipmentOrderSchema)
    @permission_required('logistics:shipment:update')
    def put(self, shipment_id, data):
        """更新发货单"""
        shipment = ShipmentService.update_shipment(shipment_id, data)
        return {'data': shipment}
    
    @logistics_bp.doc(summary='删除发货单', description='删除发货单')
    @permission_required('logistics:shipment:delete')
    def delete(self, shipment_id):
        """删除发货单"""
        ShipmentService.delete_shipment(shipment_id)
        return {'data': {'success': True}}


class ShipmentGenerateContractsAPI(MethodView):
    """发货单生成交付合同API"""
    decorators = [logistics_bp.auth_required(auth)]
    
    @logistics_bp.doc(
        summary='生成交付合同',
        description='从发货单按供应商自动拆分生成交付合同'
    )
    @permission_required('logistics:shipment:generate_contracts')
    def post(self, shipment_id):
        """生成交付合同"""
        user_id = get_jwt_identity()
        contracts = ShipmentService.generate_delivery_contracts(
            shipment_id=shipment_id,
            created_by=user_id
        )
        
        # 返回格式：框架会自动包装到data中
        return {
            'success': True,
            'contract_count': len(contracts),
            'contracts': [
                {
                    'id': c.id,
                    'contract_no': c.contract_no,
                    'supplier_id': c.supplier_id,
                    'total_amount': float(c.total_amount)
                }
                for c in contracts
            ]
        }


# 注册路由
logistics_bp.add_url_rule(
    '/shipments',
    view_func=ShipmentOrderListAPI.as_view('shipment_list'),
    methods=['GET', 'POST']
)

logistics_bp.add_url_rule(
    '/shipments/<int:shipment_id>',
    view_func=ShipmentOrderItemAPI.as_view('shipment_item'),
    methods=['GET', 'PUT', 'DELETE']
)

logistics_bp.add_url_rule(
    '/shipments/<int:shipment_id>/generate-contracts',
    view_func=ShipmentGenerateContractsAPI.as_view('shipment_generate_contracts'),
    methods=['POST']
)


class ShipmentConfirmAPI(MethodView):
    """发货单确认API"""
    decorators = [logistics_bp.auth_required(auth)]
    
    @logistics_bp.doc(
        summary='确认发货单',
        description='将草稿状态的发货单确认，确认后可生成报关单和交付合同'
    )
    @logistics_bp.output(ShipmentOrderSchema)
    @permission_required('logistics:shipment:confirm')
    def post(self, shipment_id):
        """确认发货单"""
        shipment = ShipmentService.confirm_shipment(shipment_id)
        return {'data': shipment}


class ShipmentSuppliersPreviewAPI(MethodView):
    """发货单供应商拆分预览API"""
    decorators = [logistics_bp.auth_required(auth)]
    
    @logistics_bp.doc(
        summary='预览按供应商拆分',
        description='预览发货单按供应商拆分的结果，用于生成交付合同前的确认'
    )
    def get(self, shipment_id):
        """预览供应商拆分"""
        suppliers = ShipmentService.get_suppliers_from_shipment(shipment_id)
        
        return {
            'data': {
                'shipment_id': shipment_id,
                'supplier_count': len(suppliers),
                'suppliers': suppliers
            }
        }


logistics_bp.add_url_rule(
    '/shipments/<int:shipment_id>/confirm',
    view_func=ShipmentConfirmAPI.as_view('shipment_confirm'),
    methods=['POST']
)

logistics_bp.add_url_rule(
    '/shipments/<int:shipment_id>/suppliers-preview',
    view_func=ShipmentSuppliersPreviewAPI.as_view('shipment_suppliers_preview'),
    methods=['GET']
)

