from apiflask import Schema
from apiflask.fields import Integer, String, List, Boolean, Nested, DateTime, Dict
from apiflask.validators import Length, Email

# --- Permission Schemas ---

class PermissionOutSchema(Schema):
    id = Integer()
    name = String(metadata={'description': '权限标识', 'example': 'product:create'})
    description = String(metadata={'description': '权限描述'})

# --- Permission Tree Schemas ---

class PermissionActionSchema(Schema):
    id = Integer(required=True)
    code = String(required=True) # e.g. product:create
    label = String(required=True) # e.g. 创建

class PermissionGroupSchema(Schema):
    name = String(required=True)   # e.g. 商品列表
    label = String(required=True)  # e.g. 商品列表
    permissions = List(Nested(PermissionActionSchema))

class PermissionModuleSchema(Schema):
    name = String(required=True)   # e.g. 商品中心
    label = String(required=True)  # e.g. 商品中心
    children = List(Nested(PermissionGroupSchema))

# --- Data Permission Schemas ---

class DataPermMetaSchema(Schema):
    id = Integer()
    key = String()
    label = String()
    type = String()
    description = String()
    children = List(Nested(lambda: DataPermMetaSchema())) # Recursive

class RoleDataPermConfigSchema(Schema):
    category_key = String(required=True)
    target_user_ids = List(Integer(), load_default=[])
    # Map of resource_key -> scope_type ('all', 'custom')
    resource_scopes = Dict(keys=String(), values=String(), load_default={})

class RoleDataPermBulkSchema(Schema):
    # List of configs
    configs = List(Nested(RoleDataPermConfigSchema), required=True)

# --- Field Permission Schemas ---

class FieldPermMetaSchema(Schema):
    id = Integer()
    module = String()
    field_key = String()
    label = String()
    description = String()

class RoleFieldPermConfigSchema(Schema):
    field_key = String(required=True)
    is_visible = Boolean(load_default=True)
    condition = String(load_default='none') # 'none', 'follower'

class RoleFieldPermUpdateSchema(Schema):
    configs = List(Nested(RoleFieldPermConfigSchema), required=True)

# --- Role Schemas ---

class RoleBaseSchema(Schema):
    name = String(required=True, validate=Length(min=2, max=50), metadata={'description': '角色名称', 'example': 'editor'})
    description = String(metadata={'description': '角色描述'})

class RoleCreateSchema(RoleBaseSchema):
    permission_ids = List(Integer(), load_default=[], metadata={'description': '关联的权限ID列表', 'example': [1, 2]})

class RoleUpdateSchema(RoleBaseSchema):
    name = String(validate=Length(min=2, max=50)) # Optional in update usually, but here we keep validation
    permission_ids = List(Integer(), load_default=[])

class RoleOutSchema(RoleBaseSchema):
    id = Integer()
    permissions = List(Nested(PermissionOutSchema), metadata={'description': '拥有的权限列表'})

class RoleUserAddSchema(Schema):
    user_ids = List(Integer(), required=True, metadata={'description': '用户ID列表', 'example': [1, 2]})

# --- User Schemas ---

class UserBaseSchema(Schema):
    username = String(required=True, validate=Length(min=3, max=50), metadata={'description': '用户名'})
    nickname = String(load_default='', metadata={'description': '昵称/中文名', 'example': '张三'})
    email = String(required=True, validate=Email(), metadata={'description': '邮箱'})
    is_active = Boolean(load_default=True, metadata={'description': '是否激活'})

class UserCreateSchema(UserBaseSchema):
    password = String(required=True, validate=Length(min=6), metadata={'description': '密码'})
    role_ids = List(Integer(), load_default=[], metadata={'description': '关联的角色ID列表'})

class UserUpdateSchema(Schema):
    username = String(validate=Length(min=3, max=50))
    nickname = String(metadata={'description': '昵称'})
    email = String(validate=Email())
    password = String(validate=Length(min=6), load_default=None)
    is_active = Boolean()
    role_ids = List(Integer())

class UserOutSchema(UserBaseSchema):
    id = Integer()
    nickname = String(metadata={'description': '昵称'})
    created_at = DateTime()
    roles = List(Nested(RoleOutSchema(only=['id', 'name', 'description'])), metadata={'description': '所属角色'})
