from apiflask import Schema
from apiflask.fields import String, List, Integer, Boolean

class LoginInput(Schema):
    username = String(
        required=True,
        metadata={'description': '用户名', 'example': 'admin'}
    )
    password = String(
        required=True,
        metadata={'description': '密码', 'example': 'admin123'}
    )

class TokenOutput(Schema):
    access_token = String(metadata={'description': 'JWT 访问令牌 (用于 Authorization 头)', 'example': 'eyJhbG...'})
    refresh_token = String(metadata={'description': 'JWT 刷新令牌 (用于获取新 Access Token)', 'example': 'eyJhbG...'})
    username = String(metadata={'description': '当前用户名', 'example': 'admin'})
    roles = List(String(), metadata={'description': '用户角色列表', 'example': ['admin', 'editor']})
    permissions = List(String(), metadata={'description': '用户权限列表', 'example': ['product:create', 'product:delete']})

class UserBaseSchema(Schema):
    id = Integer(dump_only=True, metadata={'description': '用户ID'})
    username = String(required=True, metadata={'description': '用户名'})
    email = String(required=True, metadata={'description': '邮箱地址'})
    is_active = Boolean(metadata={'description': '账号是否启用'})
    # attribute='role_names' tells marshmallow to use user.role_names property instead of user.roles
    roles = List(String(), attribute='role_names', metadata={'description': '角色列表', 'example': ['admin']}) 
    permissions = List(String(), attribute='permissions', dump_only=True, metadata={'description': '权限列表', 'example': ['product:create']}) 

class UserCreateSchema(UserBaseSchema):
    password = String(
        required=True, 
        load_only=True,
        metadata={'description': '密码 (至少6位)', 'example': 'secret'}
    )

