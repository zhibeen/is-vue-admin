from apiflask.views import MethodView
from app.schemas.system import (
    UserManageOutSchema, UserManageCreateSchema, UserManageUpdateSchema
)
from app.schemas.pagination import PaginationQuerySchema, make_pagination_schema
from app.services.system_service import SystemService
from app.security import auth
from . import system_bp

service = SystemService()
UserPaginationSchema = make_pagination_schema(UserManageOutSchema)

class UserListAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取用户列表', description='分页获取用户列表')
    @system_bp.input(PaginationQuerySchema, location='query', arg_name='query')
    @system_bp.output(UserPaginationSchema)
    def get(self, query):
        return {'data': service.list_users(page=query['page'], per_page=query['per_page'])}

    @system_bp.doc(summary='创建用户', description='创建新用户并分配角色')
    @system_bp.input(UserManageCreateSchema, arg_name='data')
    @system_bp.output(UserManageOutSchema, status_code=201)
    def post(self, data):
        return {'data': service.create_user(data)}

class UserItemAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取用户详情')
    @system_bp.output(UserManageOutSchema)
    def get(self, user_id):
        return {'data': service.get_user(user_id)}

    @system_bp.doc(summary='更新用户', description='更新用户资料或角色')
    @system_bp.input(UserManageUpdateSchema, arg_name='data')
    @system_bp.output(UserManageOutSchema)
    def put(self, user_id, data):
        return {'data': service.update_user(user_id, data)}

    @system_bp.doc(summary='删除用户')
    def delete(self, user_id):
        service.delete_user(user_id)
        return {'code': 0, 'message': 'success', 'data': None}

system_bp.add_url_rule('/users', view_func=UserListAPI.as_view('users'))
system_bp.add_url_rule('/users/<int:user_id>', view_func=UserItemAPI.as_view('user_item'))

