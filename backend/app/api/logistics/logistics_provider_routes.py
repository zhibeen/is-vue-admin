"""物流服务商API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from app.security import auth
from app.decorators import permission_required
from app.schemas.logistics.logistics_provider import (
    LogisticsProviderSchema,
    LogisticsProviderCreateSchema,
    LogisticsProviderUpdateSchema
)
from app.services.logistics.logistics_provider_service import LogisticsProviderService


logistics_provider_bp = APIBlueprint(
    'logistics_providers', 
    __name__, 
    url_prefix='/logistics-providers', 
    tag='物流服务商管理'
)


class LogisticsProviderListAPI(MethodView):
    """物流服务商列表API"""
    decorators = [logistics_provider_bp.auth_required(auth)]
    
    @logistics_provider_bp.doc(
        summary='获取物流服务商列表',
        description='获取所有物流服务商，支持按启用状态和服务类型筛选'
    )
    @logistics_provider_bp.output(LogisticsProviderSchema(many=True))
    def get(self):
        """获取物流服务商列表"""
        # TODO: 支持查询参数筛选（is_active, service_type）
        providers = LogisticsProviderService.get_all_providers()
        return {'data': providers}
    
    @logistics_provider_bp.doc(
        summary='创建物流服务商',
        description='创建新的物流服务商'
    )
    @logistics_provider_bp.input(LogisticsProviderCreateSchema, arg_name='data')
    @logistics_provider_bp.output(LogisticsProviderSchema, status_code=201)
    @permission_required('logistics:provider:create')
    def post(self, data):
        """创建物流服务商"""
        provider = LogisticsProviderService.create_provider(data)
        return {'data': provider}


class LogisticsProviderItemAPI(MethodView):
    """物流服务商详情API"""
    decorators = [logistics_provider_bp.auth_required(auth)]
    
    @logistics_provider_bp.doc(
        summary='获取物流服务商详情',
        description='根据ID获取物流服务商详细信息'
    )
    @logistics_provider_bp.output(LogisticsProviderSchema)
    def get(self, provider_id: int):
        """获取物流服务商详情"""
        provider = LogisticsProviderService.get_provider_by_id(provider_id)
        if not provider:
            return {'error': '服务商不存在'}, 404
        return {'data': provider}
    
    @logistics_provider_bp.doc(
        summary='更新物流服务商',
        description='更新物流服务商信息'
    )
    @logistics_provider_bp.input(LogisticsProviderUpdateSchema, arg_name='data')
    @logistics_provider_bp.output(LogisticsProviderSchema)
    @permission_required('logistics:provider:update')
    def put(self, provider_id: int, data):
        """更新物流服务商"""
        provider = LogisticsProviderService.update_provider(provider_id, data)
        return {'data': provider}
    
    @logistics_provider_bp.doc(
        summary='删除物流服务商',
        description='删除物流服务商（软删除）'
    )
    @logistics_provider_bp.output({}, status_code=204)
    @permission_required('logistics:provider:delete')
    def delete(self, provider_id: int):
        """删除物流服务商"""
        LogisticsProviderService.delete_provider(provider_id)
        return None


class LogisticsProviderToggleAPI(MethodView):
    """物流服务商启用/停用API"""
    decorators = [logistics_provider_bp.auth_required(auth)]
    
    @logistics_provider_bp.doc(
        summary='切换物流服务商启用状态',
        description='启用或停用物流服务商'
    )
    @logistics_provider_bp.output(LogisticsProviderSchema)
    @permission_required('logistics:provider:update')
    def post(self, provider_id: int):
        """切换启用状态"""
        provider = LogisticsProviderService.toggle_active_status(provider_id)
        return {'data': provider}


# 注册路由
logistics_provider_bp.add_url_rule(
    '',
    view_func=LogisticsProviderListAPI.as_view('list'),
    methods=['GET', 'POST']
)

logistics_provider_bp.add_url_rule(
    '/<int:provider_id>',
    view_func=LogisticsProviderItemAPI.as_view('item'),
    methods=['GET', 'PUT', 'DELETE']
)

logistics_provider_bp.add_url_rule(
    '/<int:provider_id>/toggle',
    view_func=LogisticsProviderToggleAPI.as_view('toggle'),
    methods=['POST']
)

