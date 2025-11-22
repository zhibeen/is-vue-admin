from apiflask import Schema
from apiflask.fields import Integer, String, Boolean, List, Nested, Dict, Float
from apiflask.validators import Length, OneOf

# --- Metadata Schemas ---

class AttributeOptionSchema(Schema):
    label = String()
    value = String()

class AttributeDefinitionSchema(Schema):
    id = Integer(dump_only=True)
    key_name = String()
    label = String()
    data_type = String(validate=OneOf(['text', 'number', 'select', 'boolean']))
    options = List(Nested(AttributeOptionSchema))
    is_global = Boolean()

class CategoryAttributeSchema(Schema):
    attribute = Nested(AttributeDefinitionSchema, attribute='attribute_definition')
    is_required = Boolean()
    display_order = Integer()

# --- Category Schemas ---

class CategoryBaseSchema(Schema):
    id = Integer(dump_only=True)
    name = String(required=True, validate=Length(min=1))
    code = String(validate=Length(max=10))
    is_leaf = Boolean()

class CategoryTreeSchema(CategoryBaseSchema):
    children = List(Nested(lambda: CategoryTreeSchema()))  # Recursive

class CategoryDetailSchema(CategoryBaseSchema):
    parent_id = Integer()
    # attributes = List(Nested(CategoryAttributeSchema)) # Full details only when needed

# --- VehicleAux Schemas ---

class VehicleAuxSchema(Schema):
    id = Integer(dump_only=True)
    name = String()
    level_type = String()
    full_path = String()
    parent_id = Integer()

# --- Product Schemas ---

class ProductFitmentIn(Schema):
    vehicle_id = Integer(required=True)
    notes = String()

class ProductBaseSchema(Schema):
    name = String(required=True)
    feature_code = String()
    category_id = Integer(required=True)
    
    # Physical
    length = Float()
    width = Float()
    height = Float()
    weight = Float()
    
    # Dynamic Attributes
    attributes = Dict() # {"voltage": "12V"}

class ProductCreateSchema(ProductBaseSchema):
    parent_sku_id = Integer(load_default=None)
    suffix_code = String(load_default=None)
    fitments = List(Nested(ProductFitmentIn), load_default=[])

class ProductUpdateSchema(ProductBaseSchema):
    category_id = Integer(dump_default=None) # Optional on update

class ProductOutSchema(ProductBaseSchema):
    id = Integer()
    sku = String()
    created_at = String()
    updated_at = String()
    # category = Nested(CategoryBaseSchema)

