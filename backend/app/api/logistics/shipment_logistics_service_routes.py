"""发货单物流服务明细API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.security import auth
from app.decorators import permission_required
from app.schemas.logistics.shipment_logistics_service import (
    ShipmentLogisticsServiceSchema,
    ShipmentLogisticsServiceCreateSchema,
    ShipmentLogisticsServiceUpdateSchema
)
from app.services.logistics.shipment_logistics_service import ShipmentLogisticsServiceService


shipment_logistics_service_bp = APIBlueprint(
    'shipment_logistics_services', 
    __name__, 
    url_prefix='/shipments/<int:shipment_id>/logistics-services',
    tag='发货单物流服务'
)


class ShipmentLogisticsServiceListAPI(MethodView):
    """发货单物流服务列表API"""
    decorators = [shipment_logistics_service_bp.auth_required(auth)]
    
    @shipment_logistics_service_bp.doc(
        summary='获取发货单的物流服务列表',
        description='获取指定发货单的所有物流服务明细'
    )
    @shipment_logistics_service_bp.output(ShipmentLogisticsServiceSchema(many=True))
    def get(self, shipment_id: int):
        """获取物流服务列表"""
        services = ShipmentLogisticsServiceService.get_services_by_shipment(shipment_id)
        return {'data': services}
    
    @shipment_logistics_service_bp.doc(
        summary='为发货单添加物流服务',
        description='为指定发货单添加新的物流服务明细'
    )
    @shipment_logistics_service_bp.input(ShipmentLogisticsServiceCreateSchema, arg_name='data')
    @shipment_logistics_service_bp.output(ShipmentLogisticsServiceSchema, status_code=201)
    @permission_required('logistics:service:create')
    def post(self, shipment_id: int, data):
        """添加物流服务"""
        service = ShipmentLogisticsServiceService.add_service(shipment_id, data)
        return {'data': service}


class ShipmentLogisticsServiceItemAPI(MethodView):
    """发货单物流服务详情API"""
    decorators = [shipment_logistics_service_bp.auth_required(auth)]
    
    @shipment_logistics_service_bp.doc(
        summary='获取物流服务详情',
        description='根据ID获取物流服务详细信息'
    )
    @shipment_logistics_service_bp.output(ShipmentLogisticsServiceSchema)
    def get(self, shipment_id: int, service_id: int):
        """获取物流服务详情"""
        service = ShipmentLogisticsServiceService.get_service_by_id(service_id)
        if not service or service.shipment_id != shipment_id:
            return {'error': '物流服务不存在'}, 404
        return {'data': service}
    
    @shipment_logistics_service_bp.doc(
        summary='更新物流服务',
        description='更新物流服务信息'
    )
    @shipment_logistics_service_bp.input(ShipmentLogisticsServiceUpdateSchema, arg_name='data')
    @shipment_logistics_service_bp.output(ShipmentLogisticsServiceSchema)
    @permission_required('logistics:service:update')
    def put(self, shipment_id: int, service_id: int, data):
        """更新物流服务"""
        service = ShipmentLogisticsServiceService.update_service(service_id, data)
        return {'data': service}
    
    @shipment_logistics_service_bp.doc(
        summary='删除物流服务',
        description='删除物流服务记录'
    )
    @shipment_logistics_service_bp.output({}, status_code=204)
    @permission_required('logistics:service:delete')
    def delete(self, shipment_id: int, service_id: int):
        """删除物流服务"""
        ShipmentLogisticsServiceService.delete_service(service_id)
        return None


class ShipmentLogisticsServiceConfirmAPI(MethodView):
    """物流服务确认API"""
    decorators = [shipment_logistics_service_bp.auth_required(auth)]
    
    @shipment_logistics_service_bp.doc(
        summary='确认物流服务',
        description='将物流服务状态设置为已确认'
    )
    @shipment_logistics_service_bp.output(ShipmentLogisticsServiceSchema)
    @permission_required('logistics:service:confirm')
    def post(self, shipment_id: int, service_id: int):
        """确认物流服务"""
        service = ShipmentLogisticsServiceService.confirm_service(service_id)
        return {'data': service}


class ShipmentLogisticsCostAPI(MethodView):
    """物流成本汇总API"""
    decorators = [shipment_logistics_service_bp.auth_required(auth)]
    
    @shipment_logistics_service_bp.doc(
        summary='计算发货单物流总成本',
        description='汇总计算发货单的所有物流服务费用'
    )
    def get(self, shipment_id: int):
        """计算物流总成本"""
        total_cost = ShipmentLogisticsServiceService.calculate_total_cost(shipment_id)
        return {
            'data': {
                'shipment_id': shipment_id,
                'total_logistics_cost': float(total_cost),
                'currency': 'CNY'
            }
        }


# 注册路由
shipment_logistics_service_bp.add_url_rule(
    '',
    view_func=ShipmentLogisticsServiceListAPI.as_view('list'),
    methods=['GET', 'POST']
)

shipment_logistics_service_bp.add_url_rule(
    '/<int:service_id>',
    view_func=ShipmentLogisticsServiceItemAPI.as_view('item'),
    methods=['GET', 'PUT', 'DELETE']
)

shipment_logistics_service_bp.add_url_rule(
    '/<int:service_id>/confirm',
    view_func=ShipmentLogisticsServiceConfirmAPI.as_view('confirm'),
    methods=['POST']
)

shipment_logistics_service_bp.add_url_rule(
    '/total-cost',
    view_func=ShipmentLogisticsCostAPI.as_view('total_cost'),
    methods=['GET']
)

