"""发货单相关API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from flask_jwt_extended import get_jwt_identity

from app.security import auth
from app.decorators import permission_required
from app.schemas.logistics.shipment import (
    ShipmentOrderSchema,
    ShipmentOrderCreateSchema,
    ShipmentOrderUpdateSchema
)
from app.schemas.pagination import PaginationQuerySchema, PaginationSchema
from app.services.logistics.shipment_service import ShipmentService
from app.models.logistics.shipment import ShipmentOrder

logistics_bp = APIBlueprint('logistics', __name__, url_prefix='/logistics', tag='物流管理')


class ShipmentOrderListAPI(MethodView):
    """发货单列表API"""
    decorators = [logistics_bp.auth_required(auth)]
    
    @logistics_bp.doc(summary='获取发货单列表', description='支持分页查询')
    @logistics_bp.input(PaginationQuerySchema, location='query', arg_name='pagination')
    @logistics_bp.output(PaginationSchema)
    def get(self, pagination):
        """获取发货单列表"""
        page = pagination['page']
        per_page = pagination['per_page']
        
        query = ShipmentOrder.query.order_by(ShipmentOrder.created_at.desc())
        
        # 搜索过滤
        if pagination.get('q'):
            q = f"%{pagination['q']}%"
            query = query.filter(
                ShipmentOrder.shipment_no.ilike(q) |
                ShipmentOrder.external_order_no.ilike(q)
            )
        
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
        return shipment


class ShipmentOrderItemAPI(MethodView):
    """发货单详情API"""
    decorators = [logistics_bp.auth_required(auth)]
    
    @logistics_bp.doc(summary='获取发货单详情', description='根据ID获取发货单详细信息')
    @logistics_bp.output(ShipmentOrderSchema)
    def get(self, shipment_id):
        """获取发货单详情"""
        shipment = ShipmentService.get_shipment_by_id(shipment_id)
        if not shipment:
            return {'message': '发货单不存在'}, 404
        return shipment
    
    @logistics_bp.doc(summary='更新发货单', description='更新发货单信息')
    @logistics_bp.input(ShipmentOrderUpdateSchema, arg_name='data')
    @logistics_bp.output(ShipmentOrderSchema)
    @permission_required('logistics:shipment:update')
    def put(self, shipment_id, data):
        """更新发货单"""
        shipment = ShipmentService.update_shipment(shipment_id, data)
        return shipment
    
    @logistics_bp.doc(summary='删除发货单', description='删除发货单')
    @permission_required('logistics:shipment:delete')
    def delete(self, shipment_id):
        """删除发货单"""
        ShipmentService.delete_shipment(shipment_id)
        return None


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
        
        return {
            'data': {
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

