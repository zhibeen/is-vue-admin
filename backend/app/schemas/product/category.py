from apiflask import Schema
from apiflask.fields import Integer, String, List, Boolean, Nested, DateTime, Dict

class AttributeDefinitionSchema(Schema):
    id = Integer()
    name = String()
    code = String()
    type = String()
    options = List(String())
    is_required = Boolean()
    description = String()

class CategoryBaseSchema(Schema):
    name = String(required=True)
    code = String(required=True)
    parent_id = Integer()
    description = String()
    icon = String()
    # missing -> load_default
    is_active = Boolean(load_default=True)
    sort_order = Integer(load_default=0)

class CategoryDetailSchema(CategoryBaseSchema):
    id = Integer()
    path = String()
    level = Integer()
    created_at = DateTime()
    updated_at = DateTime()

class CategoryTreeSchema(CategoryDetailSchema):
    children = List(Nested(lambda: CategoryTreeSchema()))

