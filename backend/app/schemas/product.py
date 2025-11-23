from apiflask import Schema
from apiflask.fields import Integer, String, List, Boolean, Nested, DateTime, Dict
from .mixins import FieldPermissionMixin

# --- Product Schemas ---

class ProductBaseSchema(Schema):
    name = String(required=True)
    sku = String(required=True)
    description = String()
    
    # Sensitive Fields with Permission Metadata
    cost_price = String(metadata={
        'permission_key': 'product:cost_price', 
        'label': '采购成本',
        'description': '产品的进货成本'
    })
    
    stock_price = String(metadata={
        'permission_key': 'product:stock_price', 
        'label': '库存单价',
        'description': '库存平均单价'
    })
    
    supplier = String(metadata={
        'permission_key': 'product:supplier', 
        'label': '供应商',
        'description': '默认供应商信息'
    })

class ProductSchema(FieldPermissionMixin, ProductBaseSchema):
    id = Integer()
    created_at = DateTime()
