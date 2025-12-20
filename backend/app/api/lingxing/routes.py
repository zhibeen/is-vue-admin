"""领星API路由层

提供与领星ERP系统集成的API接口：
- 查询发货单详情
- 查询备货单详情
"""
from apiflask import APIBlueprint
from apiflask.views import MethodView

from app.security import auth
from app.decorators import permission_required
from app.schemas.lingxing import (
    ShipmentDetailQuerySchema,
    ShipmentDetailSchema,
    StockDetailQuerySchema,
    StockDetailSchema
)
from app.services.lingxing import LingxingService
from app.errors import BusinessError

lingxing_bp = APIBlueprint(
    'lingxing',
    __name__,
    url_prefix='/lingxing',
    tag='领星ERP集成'
)


class ShipmentDetailAPI(MethodView):
    """发货单详情API"""
    decorators = [lingxing_bp.auth_required(auth)]
    
    @lingxing_bp.doc(
        summary='查询发货单详情',
        description='从领星ERP查询FBA发货单的详细信息，包括发货计划、商品明细、物流状态等'
    )
    @lingxing_bp.input(ShipmentDetailQuerySchema, location='query', arg_name='params')
    @lingxing_bp.output(ShipmentDetailSchema)
    @permission_required('lingxing:shipment:view')
    def get(self, params):
        """
        查询发货单详情
        
        需要权限: lingxing:shipment:view
        """
        try:
            # 调用服务层
            result = LingxingService.get_shipment_detail(
                shipment_id=params['shipment_id'],
                page=params.get('page', 1),
                page_size=params.get('page_size', 20)
            )
            
            # 返回数据（框架会自动包装到 data 字段）
            return result
            
        except BusinessError:
            # 业务错误直接抛出
            raise
        except Exception as e:
            # 其他未预期的错误
            raise BusinessError(f'查询发货单失败: {str(e)}', code=500)


class StockDetailAPI(MethodView):
    """备货单详情API"""
    decorators = [lingxing_bp.auth_required(auth)]
    
    @lingxing_bp.doc(
        summary='查询备货单详情',
        description='从领星ERP查询海外仓备货单详情，包括备货计划、库存分配、商品明细等'
    )
    @lingxing_bp.input(StockDetailQuerySchema, location='query', arg_name='params')
    @lingxing_bp.output(StockDetailSchema)
    @permission_required('lingxing:stock:view')
    def get(self, params):
        """
        查询备货单详情
        
        需要权限: lingxing:stock:view
        """
        try:
            # 调用服务层
            result = LingxingService.get_stock_detail(
                stock_id=params['stock_id'],
                page=params.get('page', 1),
                page_size=params.get('page_size', 20)
            )
            
            # 返回数据（框架会自动包装到 data 字段）
            return result
            
        except BusinessError:
            # 业务错误直接抛出
            raise
        except Exception as e:
            # 其他未预期的错误
            raise BusinessError(f'查询备货单失败: {str(e)}', code=500)


class LingxingHealthCheckAPI(MethodView):
    """领星API健康检查"""
    decorators = [lingxing_bp.auth_required(auth)]
    
    @lingxing_bp.doc(
        summary='领星API连接测试',
        description='测试领星API配置是否正确，连接是否正常'
    )
    @permission_required('lingxing:health:check')
    def get(self):
        """
        健康检查
        
        需要权限: lingxing:health:check
        """
        is_connected = LingxingService.test_connection()
        
        return {
            'data': {
                'status': 'connected' if is_connected else 'disconnected',
                'is_healthy': is_connected,
                'message': '领星API连接正常' if is_connected else '领星API配置不完整或连接失败'
            }
        }


# 注册路由
lingxing_bp.add_url_rule(
    '/shipments/detail',
    view_func=ShipmentDetailAPI.as_view('shipment_detail'),
    methods=['GET']
)

lingxing_bp.add_url_rule(
    '/stocks/detail',
    view_func=StockDetailAPI.as_view('stock_detail'),
    methods=['GET']
)

lingxing_bp.add_url_rule(
    '/health',
    view_func=LingxingHealthCheckAPI.as_view('health_check'),
    methods=['GET']
)

