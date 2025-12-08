from apiflask import Schema
from apiflask.fields import Integer, String, Boolean, Dict as DictField

class ProductBusinessRuleSchema(Schema):
    id = Integer(dump_only=True)
    business_type = String(required=True)
    name = String(required=True)
    generate_strategy = String(required=True)
    sku_prefix = String(allow_none=True)
    requires_audit = Boolean()
    config = DictField(allow_none=True)

