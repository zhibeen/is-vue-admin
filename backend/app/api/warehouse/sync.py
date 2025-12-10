from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.schemas.warehouse import (
    StockDiscrepancySchema, StockDiscrepancyResolveSchema
)
from app.schemas.pagination import make_pagination_schema, PaginationQuerySchema
from app.services.warehouse import SyncService
from app.security import auth
from app.decorators import permission_required
from flask_jwt_extended import get_jwt_identity
from app.tasks import sync_all_third_party_warehouses as sync_all_task

# 同步管理Blueprint
sync_bp = APIBlueprint('sync', __name__, url_prefix='/sync', tag='同步管理')

# 创建服务实例
sync_service = SyncService()

# 创建分页Schema
StockDiscrepancyPaginationSchema = make_pagination_schema(StockDiscrepancySchema)


class SyncWarehouseAPI(MethodView):
    """同步仓库API"""
    decorators = [sync_bp.auth_required(auth)]
    
    @sync_bp.doc(summary='同步仓库库存', description='同步指定第三方仓库的库存')
    @sync_bp.output({'data': {'type': 'object'}})
    @permission_required('sync:execute')
    def post(self, warehouse_id):
        """同步仓库库存"""
        result = sync_service.sync_warehouse_stock(warehouse_id)
        return {'data': result}


class SyncAllAPI(MethodView):
    """同步所有仓库API"""
    decorators = [sync_bp.auth_required(auth)]
    
    @sync_bp.doc(summary='同步所有第三方仓库', description='异步同步所有第三方仓库的库存')
    @sync_bp.output({'task_id': {'type': 'string'}})
    @permission_required('sync:execute')
    def post(self):
        """同步所有第三方仓库"""
        # 异步执行同步任务
        task = sync_all_task.delay()
        return {'data': {'task_id': task.id}}


class StockDiscrepancyListAPI(MethodView):
    """库存差异列表API"""
    decorators = [sync_bp.auth_required(auth)]
    
    @sync_bp.doc(summary='获取库存差异列表', description='获取库存差异记录列表')
    @sync_bp.input(PaginationQuerySchema, location='query', arg_name='query_data')
    @sync_bp.output(StockDiscrepancyPaginationSchema)
    @permission_required('sync:view')
    def get(self, query_data):
        """获取库存差异列表"""
        result = sync_service.get_discrepancies(
            page=query_data.get('page', 1),
            per_page=query_data.get('per_page', 50),
            warehouse_id=query_data.get('warehouse_id'),
            sku=query_data.get('sku'),
            status=query_data.get('status'),
            start_date=query_data.get('start_date'),
            end_date=query_data.get('end_date')
        )
        return result


class StockDiscrepancyResolveAPI(MethodView):
    """解决库存差异API"""
    decorators = [sync_bp.auth_required(auth)]
    
    @sync_bp.doc(summary='解决库存差异', description='解决库存差异记录')
    @sync_bp.input(StockDiscrepancyResolveSchema, arg_name='data')
    @sync_bp.output(StockDiscrepancySchema)
    @permission_required('sync:resolve')
    def post(self, discrepancy_id, data):
        """解决库存差异"""
        user_id = get_jwt_identity()
        discrepancy = sync_service.resolve_discrepancy(discrepancy_id, data, user_id)
        return discrepancy


class ThirdPartyWarehouseListAPI(MethodView):
    """第三方仓库列表API"""
    decorators = [sync_bp.auth_required(auth)]
    
    @sync_bp.doc(summary='获取第三方仓库列表', description='获取所有第三方仓库列表')
    @sync_bp.output({'items': {'type': 'array', 'items': {'type': 'object'}}})
    @permission_required('sync:view')
    def get(self):
        """获取第三方仓库列表"""
        warehouses = sync_service.get_third_party_warehouses()
        return {'data': {'items': warehouses}}


# 注册路由
sync_bp.add_url_rule('/warehouses/<int:warehouse_id>', view_func=SyncWarehouseAPI.as_view('sync_warehouse'))
sync_bp.add_url_rule('/all', view_func=SyncAllAPI.as_view('sync_all'))
sync_bp.add_url_rule('/discrepancies', view_func=StockDiscrepancyListAPI.as_view('stock_discrepancy_list'))
sync_bp.add_url_rule('/discrepancies/<int:discrepancy_id>/resolve', view_func=StockDiscrepancyResolveAPI.as_view('stock_discrepancy_resolve'))
sync_bp.add_url_rule('/third-party-warehouses', view_func=ThirdPartyWarehouseListAPI.as_view('third_party_warehouse_list'))
