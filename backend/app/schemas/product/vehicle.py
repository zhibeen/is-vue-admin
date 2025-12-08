from apiflask import Schema
from apiflask.fields import Integer, String, List, Boolean, Nested

class ProductVehicleBaseSchema(Schema):
    id = Integer(dump_only=True)
    parent_id = Integer()
    name = String(required=True)
    
    # Updated fields
    abbreviation = String(required=True, metadata={'description': 'SPU Abbreviation (CHE, SIL)'})
    code = String(load_default=None, metadata={'description': 'Standard Code (12, 5890)'})
    
    level_type = String(required=True)
    sort_order = Integer()
    is_active = Boolean()

class ProductVehicleTreeSchema(ProductVehicleBaseSchema):
    children = List(Nested(lambda: ProductVehicleTreeSchema()))
