from apiflask.views import MethodView
from app.schemas.system import (
    RoleOutSchema, RoleCreateSchema, RoleUpdateSchema, PermissionOutSchema,
    PermissionModuleSchema, RoleUserAddSchema, UserOutSchema,
    DataPermMetaSchema, RoleDataPermConfigSchema, RoleDataPermBulkSchema,
    FieldPermMetaSchema, RoleFieldPermUpdateSchema, RoleFieldPermConfigSchema
)
from app.services.system_service import SystemService
from app.security import auth
from . import system_bp

service = SystemService()

# --- Field Permission APIs ---

class FieldPermMetaListAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取字段权限元数据')
    @system_bp.output(FieldPermMetaSchema(many=True))
    def get(self):
        return {'data': service.get_field_permission_metas()}

class RoleFieldPermissionAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取角色字段权限配置')
    @system_bp.output(RoleFieldPermConfigSchema(many=True))
    def get(self, role_id):
        return {'data': service.get_role_field_permissions(role_id)}

    @system_bp.doc(summary='保存角色字段权限配置')
    @system_bp.input(RoleFieldPermUpdateSchema, arg_name='data')
    @system_bp.output(RoleFieldPermConfigSchema(many=True))
    def post(self, role_id, data):
        # data['configs'] is the list
        return {'data': service.save_role_field_permissions(role_id, data['configs'])}

# --- Data Permission APIs ---

class DataPermMetaListAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取数据权限元数据', description='获取数据权限的层级结构（Category -> Module -> Resource）')
    @system_bp.output(DataPermMetaSchema(many=True))
    def get(self):
        return service.get_data_permission_metas()

class RoleDataPermissionAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取角色数据权限配置')
    @system_bp.output(RoleDataPermConfigSchema)
    def get(self, role_id):
        # Need category_key from query params
        from flask import request
        category_key = request.args.get('category_key')
        if not category_key:
            # Should we return 400? Or default?
            # Let's require it for now as the frontend will switch tabs.
            from apiflask import abort
            abort(400, 'category_key is required')
            
        return {'data': service.get_role_data_permission(role_id, category_key)}

    @system_bp.doc(summary='保存角色数据权限配置')
    @system_bp.input(RoleDataPermConfigSchema, arg_name='data')
    @system_bp.output(RoleDataPermConfigSchema)
    def post(self, role_id, data):
        return {'data': service.save_role_data_permission(role_id, data)}

class RoleDataPermBulkAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='批量保存角色数据权限配置')
    @system_bp.input(RoleDataPermBulkSchema, arg_name='data')
    def post(self, role_id, data):
        service.save_role_data_permissions_bulk(role_id, data['configs'])
        return {
            'code': 0,
            'message': 'success',
            'data': None
        }

class PermissionListAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取所有权限', description='获取系统所有可用的权限列表')
    @system_bp.output(PermissionOutSchema(many=True))
    def get(self):
        return {'data': service.list_permissions()}

class PermissionTreeAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取权限树', description='获取结构化的权限树，用于前端角色管理界面的权限勾选表格。')
    @system_bp.output(PermissionModuleSchema(many=True))
    def get(self):
        return service.get_permission_tree()

class RoleListAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取角色列表', description='获取所有角色及其关联的权限')
    @system_bp.output(RoleOutSchema(many=True))
    def get(self):
        return {'data': service.list_roles()}

    @system_bp.doc(summary='创建角色', description='创建新角色并分配权限')
    @system_bp.input(RoleCreateSchema, arg_name='data')
    @system_bp.output(RoleOutSchema, status_code=201)
    def post(self, data):
        return {'data': service.create_role(data)}

class RoleItemAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取角色详情')
    @system_bp.output(RoleOutSchema)
    def get(self, role_id):
        return {'data': service.get_role(role_id)}

    @system_bp.doc(summary='更新角色', description='更新角色名称、描述或权限列表')
    @system_bp.input(RoleUpdateSchema, arg_name='data')
    @system_bp.output(RoleOutSchema)
    def put(self, role_id, data):
        return {'data': service.update_role(role_id, data)}

    @system_bp.doc(summary='删除角色')
    def delete(self, role_id):
        service.delete_role(role_id)
        return {
            'code': 0,
            'message': 'success',
            'data': None
        }

class RoleUsersAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取角色下的用户')
    def get(self, role_id):
        # 获取查询参数
        from flask import request
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        q = request.args.get('q', None, type=str)
        
        result = service.get_role_users(role_id, page, per_page, q)
        # 手动序列化 items
        serialized_items = UserOutSchema(many=True).dump(result['items'])
        result['items'] = serialized_items
        
        # APIFlask BaseResponseSchema is only applied when @output is used.
        # Since we don't have @output here, we must return the full structure manually
        # to satisfy the frontend interceptor.
        return {
            'code': 0,
            'message': 'success',
            'data': result
        }

    @system_bp.doc(summary='批量添加用户到角色')
    @system_bp.input(RoleUserAddSchema, arg_name='data')
    def post(self, role_id, data):
        service.add_users_to_role(role_id, data['user_ids'])
        return {
            'code': 0,
            'message': 'success',
            'data': None
        } 

class RoleUserItemAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]

    @system_bp.doc(summary='从角色移除用户')
    def delete(self, role_id, user_id):
        service.remove_user_from_role(role_id, user_id)
        return {
            'code': 0,
            'message': 'success',
            'data': None
        }

system_bp.add_url_rule('/field-permission-metas', view_func=FieldPermMetaListAPI.as_view('field_permission_metas'))
system_bp.add_url_rule('/roles/<int:role_id>/field-permissions', view_func=RoleFieldPermissionAPI.as_view('role_field_permissions'))

system_bp.add_url_rule('/data-permission-metas', view_func=DataPermMetaListAPI.as_view('data_permission_metas'))
system_bp.add_url_rule('/roles/<int:role_id>/data-permissions', view_func=RoleDataPermissionAPI.as_view('role_data_permissions'))
system_bp.add_url_rule('/roles/<int:role_id>/data-permissions/bulk', view_func=RoleDataPermBulkAPI.as_view('role_data_permissions_bulk'))

system_bp.add_url_rule('/permissions', view_func=PermissionListAPI.as_view('permissions'))
system_bp.add_url_rule('/permissions/tree', view_func=PermissionTreeAPI.as_view('permission_tree'))
system_bp.add_url_rule('/roles', view_func=RoleListAPI.as_view('roles'))
system_bp.add_url_rule('/roles/<int:role_id>', view_func=RoleItemAPI.as_view('role_item'))
system_bp.add_url_rule('/roles/<int:role_id>/users', view_func=RoleUsersAPI.as_view('role_users'))
system_bp.add_url_rule('/roles/<int:role_id>/users/<int:user_id>', view_func=RoleUserItemAPI.as_view('role_user_item'))
