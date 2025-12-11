from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.schemas.warehouse import (
    StockSchema, StockQuerySchema, StockAdjustSchema,
    StockMovementSchema, StockMovementQuerySchema
)
from app.schemas.pagination import make_pagination_schema, PaginationQuerySchema
from app.services.warehouse import StockService
from app.security import auth
from app.decorators import permission_required
from flask_jwt_extended import get_jwt_identity

# 库存管理Blueprint
stock_bp = APIBlueprint('stock', __name__, url_prefix='/stocks', tag='库存管理')

# 创建服务实例
stock_service = StockService()

# 创建分页Schema
StockPaginationSchema = make_pagination_schema(StockSchema)
StockMovementPaginationSchema = make_pagination_schema(StockMovementSchema)


class StockListAPI(MethodView):
    """库存列表API"""
    decorators = [stock_bp.auth_required(auth)]
    
    @stock_bp.doc(summary='获取库存列表', description='获取库存列表，支持分页、搜索和过滤')
    @stock_bp.input(StockQuerySchema, location='query', arg_name='query_data')
    @stock_bp.output(StockPaginationSchema)
    @permission_required('stock:view')
    def get(self, query_data):
        """获取库存列表"""
        result = stock_service.get_stock_list(
            page=query_data.get('page', 1),
            per_page=query_data.get('per_page', 20),
            sku=query_data.get('sku'),
            warehouse_id=query_data.get('warehouse_id'),
            batch_no=query_data.get('batch_no'),
            min_quantity=query_data.get('min_quantity'),
            max_quantity=query_data.get('max_quantity')
        )
        return {'data': result}


class StockItemAPI(MethodView):
    """单个库存API"""
    decorators = [stock_bp.auth_required(auth)]
    
    @stock_bp.doc(summary='获取库存详情', description='根据SKU和仓库ID获取库存详细信息')
    @stock_bp.output(StockSchema)
    @permission_required('stock:view')
    def get(self, sku, warehouse_id):
        """获取库存详情"""
        stock = stock_service.get_stock(sku, warehouse_id)
        return {'data': stock}


class StockAdjustAPI(MethodView):
    """库存调整API"""
    decorators = [stock_bp.auth_required(auth)]
    
    @stock_bp.doc(summary='调整库存', description='入库、出库、调拨、调整库存')
    @stock_bp.input(StockAdjustSchema, arg_name='data')
    @stock_bp.output(StockSchema)
    @permission_required('stock:adjust')
    def post(self, data):
        """调整库存"""
        user_id = get_jwt_identity()
        stock = stock_service.adjust_stock(data, user_id)
        return {'data': stock}


class StockMovementListAPI(MethodView):
    """库存流水列表API"""
    decorators = [stock_bp.auth_required(auth)]
    
    @stock_bp.doc(summary='获取库存流水', description='获取库存流水记录，支持分页和过滤')
    @stock_bp.input(StockMovementQuerySchema, location='query', arg_name='query_data')
    @stock_bp.output(StockMovementPaginationSchema)
    @permission_required('stock:view')
    def get(self, query_data):
        """获取库存流水"""
        result = stock_service.get_movements(
            page=query_data.get('page', 1),
            per_page=query_data.get('per_page', 50),
            sku=query_data.get('sku'),
            warehouse_id=query_data.get('warehouse_id'),
            order_type=query_data.get('order_type'),
            order_no=query_data.get('order_no'),
            start_date=query_data.get('start_date'),
            end_date=query_data.get('end_date')
        )
        return {'data': result}


class StockSummaryAPI(MethodView):
    """库存汇总API"""
    decorators = [stock_bp.auth_required(auth)]
    
    @stock_bp.doc(summary='获取库存汇总', description='获取库存汇总统计信息')
    @stock_bp.output(StockSchema)
    @permission_required('stock:view')
    def get(self):
        """获取库存汇总"""
        result = stock_service.get_stock_summary()
        return {'data': result}


class StockAllocateAPI(MethodView):
    """库存分配API"""
    decorators = [stock_bp.auth_required(auth)]
    
    @stock_bp.doc(summary='分配库存', description='分配可用库存为已分配库存')
    @stock_bp.input({'quantity': {'type': 'integer', 'required': True}}, arg_name='data')
    @stock_bp.output({'success': {'type': 'boolean'}})
    @permission_required('stock:allocate')
    def post(self, sku, warehouse_id, data):
        """分配库存"""
        success = stock_service.allocate_stock(sku, warehouse_id, data['quantity'])
        return {'data': {'success': success}}


class StockReleaseAPI(MethodView):
    """库存释放API"""
    decorators = [stock_bp.auth_required(auth)]
    
    @stock_bp.doc(summary='释放库存', description='释放已分配的库存为可用库存')
    @stock_bp.input({'quantity': {'type': 'integer', 'required': True}}, arg_name='data')
    @stock_bp.output({})
    @permission_required('stock:allocate')
    def post(self, sku, warehouse_id, data):
        """释放库存"""
        stock_service.release_stock(sku, warehouse_id, data['quantity'])
        return {'data': None}


# 注册路由
stock_bp.add_url_rule('', view_func=StockListAPI.as_view('stock_list'))
stock_bp.add_url_rule('/<string:sku>/warehouses/<int:warehouse_id>', view_func=StockItemAPI.as_view('stock_item'))
stock_bp.add_url_rule('/adjust', view_func=StockAdjustAPI.as_view('stock_adjust'))
stock_bp.add_url_rule('/movements', view_func=StockMovementListAPI.as_view('stock_movement_list'))
stock_bp.add_url_rule('/summary', view_func=StockSummaryAPI.as_view('stock_summary'))
stock_bp.add_url_rule('/<string:sku>/warehouses/<int:warehouse_id>/allocate', view_func=StockAllocateAPI.as_view('stock_allocate'))
stock_bp.add_url_rule('/<string:sku>/warehouses/<int:warehouse_id>/release', view_func=StockReleaseAPI.as_view('stock_release'))
