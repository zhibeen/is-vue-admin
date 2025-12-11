from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.schemas.warehouse import (
    WarehouseSchema, WarehouseCreateSchema, WarehouseUpdateSchema,
    WarehouseLocationSchema, WarehouseLocationCreateSchema, WarehouseLocationUpdateSchema,
    WarehouseQuerySchema, WarehouseStatsSchema  # 新增 StatsSchema
)
from app.schemas.pagination import make_pagination_schema, PaginationQuerySchema
from app.services.warehouse import WarehouseService
from app.security import auth
from app.decorators import permission_required
from flask_jwt_extended import get_jwt_identity
from app.extensions import db
from app.models.warehouse import WarehouseLocation

# 仓库管理Blueprint
warehouse_bp = APIBlueprint('warehouse', __name__, url_prefix='/warehouses', tag='仓库管理')

# 创建服务实例
warehouse_service = WarehouseService()

# 创建分页Schema
WarehousePaginationSchema = make_pagination_schema(WarehouseSchema)
WarehouseLocationPaginationSchema = make_pagination_schema(WarehouseLocationSchema)


class WarehouseStatsAPI(MethodView):
    """仓库统计API"""
    decorators = [warehouse_bp.auth_required(auth)]
    
    @warehouse_bp.doc(summary='获取仓库统计', description='获取仓库的统计数据')
    @warehouse_bp.output(WarehouseStatsSchema)
    @permission_required('warehouse:view')
    def get(self):
        """获取仓库统计"""
        stats = warehouse_service.get_stats()
        return {'data': stats}


class WarehouseListAPI(MethodView):
    """仓库列表API"""
    decorators = [warehouse_bp.auth_required(auth)]
    
    @warehouse_bp.doc(summary='获取仓库列表', description='获取仓库列表，支持分页、搜索和过滤')
    @warehouse_bp.input(WarehouseQuerySchema, location='query', arg_name='query_data')
    @warehouse_bp.output(WarehousePaginationSchema)
    @permission_required('warehouse:view')
    def get(self, query_data):
        """获取仓库列表"""
        # 处理参数名映射：前端传递keyword，后端使用q
        keyword = query_data.get('keyword') or query_data.get('q')
        
        result = warehouse_service.get_list(
            page=query_data['page'],
            per_page=query_data['per_page'],
            keyword=keyword,
            category=query_data.get('category'),
            location_type=query_data.get('location_type'),
            ownership_type=query_data.get('ownership_type'),
            status=query_data.get('status')
        )
        return {'data': result}
    
    @warehouse_bp.doc(summary='创建仓库', description='创建一个新仓库')
    @warehouse_bp.input(WarehouseCreateSchema, arg_name='data')
    @warehouse_bp.output(WarehouseSchema, status_code=201)
    @permission_required('warehouse:create')
    def post(self, data):
        """创建仓库"""
        user_id = get_jwt_identity()
        warehouse = warehouse_service.create_warehouse(data, user_id)
        return {'data': warehouse}


class WarehouseItemAPI(MethodView):
    """单个仓库API"""
    decorators = [warehouse_bp.auth_required(auth)]
    
    @warehouse_bp.doc(summary='获取仓库详情', description='根据ID获取仓库详细信息')
    @warehouse_bp.output(WarehouseSchema)
    @permission_required('warehouse:view')
    def get(self, warehouse_id):
        """获取仓库详情"""
        warehouse = warehouse_service.get_warehouse(warehouse_id)
        return {'data': warehouse}
    
    @warehouse_bp.doc(summary='更新仓库', description='更新仓库信息')
    @warehouse_bp.input(WarehouseUpdateSchema, arg_name='data')
    @warehouse_bp.output(WarehouseSchema)
    @permission_required('warehouse:update')
    def put(self, warehouse_id, data):
        """更新仓库"""
        warehouse = warehouse_service.update_warehouse(warehouse_id, data)
        return {'data': warehouse}
    
    @warehouse_bp.doc(summary='删除仓库', description='删除仓库（需确保无库存）')
    @warehouse_bp.output({})
    @permission_required('warehouse:delete')
    def delete(self, warehouse_id):
        """删除仓库"""
        warehouse_service.delete_warehouse(warehouse_id)
        return {'data': None}


class WarehouseLocationListAPI(MethodView):
    """仓库库位列表API"""
    decorators = [warehouse_bp.auth_required(auth)]
    
    @warehouse_bp.doc(summary='获取库位列表', description='获取指定仓库的库位列表')
    @warehouse_bp.input(PaginationQuerySchema, location='query', arg_name='query_data')
    @warehouse_bp.output(WarehouseLocationPaginationSchema)
    @permission_required('warehouse:view')
    def get(self, warehouse_id, query_data):
        """获取库位列表"""
        result = warehouse_service.get_locations(
            warehouse_id=warehouse_id,
            page=query_data['page'],
            per_page=query_data['per_page'],
            keyword=query_data.get('q'),
            location_type=query_data.get('type')
        )
        return {'data': result}
    
    @warehouse_bp.doc(summary='创建库位', description='为指定仓库创建新库位')
    @warehouse_bp.input(WarehouseLocationCreateSchema, arg_name='data')
    @warehouse_bp.output(WarehouseLocationSchema, status_code=201)
    @permission_required('warehouse:update')
    def post(self, warehouse_id, data):
        """创建库位"""
        user_id = get_jwt_identity()
        location = warehouse_service.create_location(warehouse_id, data, user_id)
        return {'data': location}


class WarehouseLocationItemAPI(MethodView):
    """单个库位API"""
    decorators = [warehouse_bp.auth_required(auth)]
    
    @warehouse_bp.doc(summary='获取库位详情', description='根据ID获取库位详细信息')
    @warehouse_bp.output(WarehouseLocationSchema)
    @permission_required('warehouse:view')
    def get(self, location_id):
        """获取库位详情"""
        location = db.session.get(WarehouseLocation, location_id)
        if not location:
            from app.errors import BusinessError
            raise BusinessError(f'库位 {location_id} 不存在', code=404)
        return {'data': location}
    
    @warehouse_bp.doc(summary='更新库位', description='更新库位信息')
    @warehouse_bp.input(WarehouseLocationUpdateSchema, arg_name='data')
    @warehouse_bp.output(WarehouseLocationSchema)
    @permission_required('warehouse:update')
    def put(self, location_id, data):
        """更新库位"""
        location = warehouse_service.update_location(location_id, data)
        return {'data': location}
    
    @warehouse_bp.doc(summary='删除库位', description='删除库位（需确保无库存流水）')
    @warehouse_bp.output({})
    @permission_required('warehouse:delete')
    def delete(self, location_id):
        """删除库位"""
        warehouse_service.delete_location(location_id)
        return {'data': None}


# 注册路由
warehouse_bp.add_url_rule('/stats', view_func=WarehouseStatsAPI.as_view('warehouse_stats'))
warehouse_bp.add_url_rule('', view_func=WarehouseListAPI.as_view('warehouse_list'))
warehouse_bp.add_url_rule('/<int:warehouse_id>', view_func=WarehouseItemAPI.as_view('warehouse_item'))
warehouse_bp.add_url_rule('/<int:warehouse_id>/locations', view_func=WarehouseLocationListAPI.as_view('warehouse_location_list'))
warehouse_bp.add_url_rule('/locations/<int:location_id>', view_func=WarehouseLocationItemAPI.as_view('warehouse_location_item'))
