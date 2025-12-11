from apiflask import Schema
from apiflask.fields import String, Integer, Boolean
from marshmallow import pre_load

class ThirdPartyServiceSchema(Schema):
    id = Integer(dump_only=True)
    code = String(required=True)
    name = String(required=True)
    # 不返回敏感信息
    
class ThirdPartyWarehouseSchema(Schema):
    id = Integer(dump_only=True)
    code = String()
    name = String()
    country_code = String(allow_none=True)
    is_active = Boolean()
    note = String(allow_none=True)
    last_synced_at = String(dump_only=True)
    
    # 扩展字段：前端展示用
    is_bound = Boolean(dump_default=False)
    bound_warehouse_name = String(allow_none=True)

