"""发货单采购明细API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from flask_jwt_extended import get_jwt_identity

from app.security import auth
from app.decorators import permission_required
from app.schemas.logistics.purchase_item import (
    ShipmentPurchaseItemSchema,
    ShipmentPurchaseItemCreateSchema,
    ShipmentPurchaseItemUpdateSchema
)
from app.services.logistics.purchase_item_service import ShipmentPurchaseItemService
from app.models.logistics.purchase_item import ShipmentPurchaseItem
from app.errors import BusinessError

purchase_item_bp = APIBlueprint(
    'purchase_items', 
    __name__, 
    url_prefix='/logistics/shipments',
    tag='发货单采购明细'
)


class ShipmentPurchaseItemListAPI(MethodView):
    """发货单采购明细列表API"""
    decorators = [purchase_item_bp.auth_required(auth)]
    
    @purchase_item_bp.doc(
        summary='获取采购明细列表',
        description='获取指定发货单的采购明细，支持按供应商/采购单/SKU分组'
    )
    @purchase_item_bp.input(
        {
            'type': 'object',
            'properties': {
                'group_by': {
                    'type': 'string',
                    'enum': ['supplier', 'purchase_order', 'sku'],
                    'description': '分组方式'
                }
            }
        },
        location='query',
        arg_name='query_params'
    )
    @purchase_item_bp.output(ShipmentPurchaseItemSchema(many=True))
    @permission_required('logistics:shipment:view')
    def get(self, shipment_id: int, query_params: dict):
        """获取采购明细列表"""
        group_by = query_params.get('group_by')
        items = ShipmentPurchaseItemService.get_purchase_items(shipment_id, group_by)
        
        return {'data': items}
    
    @purchase_item_bp.doc(
        summary='添加采购明细',
        description='为发货单添加采购明细，会自动更新商品明细'
    )
    @purchase_item_bp.input(ShipmentPurchaseItemCreateSchema, arg_name='data')
    @purchase_item_bp.output(ShipmentPurchaseItemSchema, status_code=201)
    @permission_required('logistics:shipment:edit')
    def post(self, shipment_id: int, data: dict):
        """添加采购明细"""
        item = ShipmentPurchaseItemService.create_purchase_item(shipment_id, data)
        return {'data': item.to_dict()}


class ShipmentPurchaseItemDetailAPI(MethodView):
    """发货单采购明细详情API"""
    decorators = [purchase_item_bp.auth_required(auth)]
    
    @purchase_item_bp.doc(
        summary='获取采购明细详情',
        description='获取指定采购明细的详细信息'
    )
    @purchase_item_bp.output(ShipmentPurchaseItemSchema)
    @permission_required('logistics:shipment:view')
    def get(self, shipment_id: int, item_id: int):
        """获取采购明细详情"""
        item = ShipmentPurchaseItem.query.filter_by(
            id=item_id,
            shipment_order_id=shipment_id
        ).first()
        
        if not item:
            raise BusinessError('采购明细不存在', code=404)
        
        return {'data': item.to_dict()}
    
    @purchase_item_bp.doc(
        summary='更新采购明细',
        description='更新采购明细信息，会自动更新商品明细'
    )
    @purchase_item_bp.input(ShipmentPurchaseItemUpdateSchema, arg_name='data')
    @purchase_item_bp.output(ShipmentPurchaseItemSchema)
    @permission_required('logistics:shipment:edit')
    def put(self, shipment_id: int, item_id: int, data: dict):
        """更新采购明细"""
        item = ShipmentPurchaseItemService.update_purchase_item(item_id, data)
        return {'data': item.to_dict()}
    
    @purchase_item_bp.doc(
        summary='删除采购明细',
        description='删除采购明细，会自动更新商品明细'
    )
    @permission_required('logistics:shipment:edit')
    def delete(self, shipment_id: int, item_id: int):
        """删除采购明细"""
        ShipmentPurchaseItemService.delete_purchase_item(item_id)
        return {'message': '采购明细删除成功'}


class ShipmentPurchaseItemRecalculateAPI(MethodView):
    """重新计算商品明细API"""
    decorators = [purchase_item_bp.auth_required(auth)]
    
    @purchase_item_bp.doc(
        summary='重新计算商品明细',
        description='基于采购明细重新计算商品明细（全量重算）'
    )
    @permission_required('logistics:shipment:edit')
    def post(self, shipment_id: int):
        """重新计算商品明细"""
        ShipmentPurchaseItemService.recalculate_all_items(shipment_id)
        return {'message': '商品明细重新计算完成'}


class ShipmentValidateAPI(MethodView):
    """发货单数据验证API"""
    decorators = [purchase_item_bp.auth_required(auth)]
    
    @purchase_item_bp.doc(
        summary='验证数据一致性',
        description='验证采购明细与商品明细的数据一致性'
    )
    @permission_required('logistics:shipment:view')
    def get(self, shipment_id: int):
        """验证数据一致性"""
        result = ShipmentPurchaseItemService.validate_shipment_consistency(shipment_id)
        return {'data': result}


# 注册路由
purchase_item_bp.add_url_rule(
    '/<int:shipment_id>/purchase-items',
    view_func=ShipmentPurchaseItemListAPI.as_view('purchase_item_list'),
    methods=['GET', 'POST']
)

purchase_item_bp.add_url_rule(
    '/<int:shipment_id>/purchase-items/<int:item_id>',
    view_func=ShipmentPurchaseItemDetailAPI.as_view('purchase_item_detail'),
    methods=['GET', 'PUT', 'DELETE']
)

purchase_item_bp.add_url_rule(
    '/<int:shipment_id>/purchase-items/recalculate',
    view_func=ShipmentPurchaseItemRecalculateAPI.as_view('purchase_item_recalculate'),
    methods=['POST']
)

purchase_item_bp.add_url_rule(
    '/<int:shipment_id>/validate',
    view_func=ShipmentValidateAPI.as_view('shipment_validate'),
    methods=['GET']
)

