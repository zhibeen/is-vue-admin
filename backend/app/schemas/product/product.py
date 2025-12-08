from apiflask import Schema
from apiflask.fields import Integer, String, List, Boolean, Nested, DateTime, Dict, Decimal as DecimalField
from app.schemas.mixins import FieldPermissionMixin

# --- Auxiliary Schemas ---

class SkuSuffixSchema(Schema):
    code = String()
    meaning_en = String()
    meaning_cn = String()
    category_ids = List(Integer(), dump_only=True)

class TaxCategorySchema(Schema):
    id = Integer()
    code = String()
    name = String()
    short_name = String()
    description = String()
    reference_rate = DecimalField()

class NextSerialSchema(Schema):
    serial = String()

class PreviewVariantSchema(Schema):
    sku = String()
    feature_code = String()
    specs = Dict()

class ProductPreviewResponseSchema(Schema):
    spu_code = String()
    variants = List(Nested(PreviewVariantSchema))

class ProductReferenceCodeSchema(Schema):
    id = Integer(dump_only=True)
    code = String(required=True)
    code_type = String(required=True, metadata={'description': 'OE, OEM, PARTSLINK'})
    brand = String()

class ProductVariantSchema(FieldPermissionMixin, Schema):
    id = Integer(dump_only=True)
    # Allow missing sku on input (will be auto-generated), but required on output
    sku = String(metadata={'description': 'System Code'}) 
    feature_code = String(metadata={'description': 'Business Feature Code'})
    supplier_sku = String()
    
    quality_type = String(metadata={'description': 'Aftermarket, OEM'})
    specs = Dict()
    
    # Commercial (Sensitive)
    price = DecimalField(metadata={'permission': 'product:price:view'})
    cost_price = DecimalField(metadata={'permission': 'product:cost:view'})
    
    # Physical
    weight = DecimalField()
    
    # Compliance
    hs_code_id = Integer()
    declared_name = String()
    declared_unit = String()
    
    created_at = DateTime(dump_only=True)

# --- Product (SPU) Schemas ---

class ProductBaseSchema(Schema):
    spu_code = String(metadata={'description': 'Internal SPU Code'})
    name = String(required=True)
    category_id = Integer(required=True)
    
    # 汽配专用字段 (Updated: remove vehicle_brand_id)
    brand_code = String(metadata={'description': '首选品牌编码 (如 22, 12)', 'load_only': True}) # 只用于接收前端参数，不返回
    
    description = String()
    main_image = String()
    attributes = Dict()
    spu_coding_metadata = Dict(allow_none=True) # New field to accept SPU params

class ProductCreateSchema(ProductBaseSchema):
    # For creating SPU, we might also accept initial variants
    variants = List(Nested(ProductVariantSchema))
    reference_codes = List(Nested(ProductReferenceCodeSchema))

    # Optional fields that might be passed by frontend but strictly belong to variants
    # We accept them here to avoid validation errors, and can use them as defaults if needed
    declared_name = String()
    declared_unit = String()

class ProductStatsSchema(Schema):
    total = Integer()
    new = Integer()
    updated = Integer()
    existing = Integer()

class ProductCreateResponseSchema(Schema):
    spu_code = String()
    action = String() # created, merged
    stats = Nested(ProductStatsSchema)
    new_variants = List(String()) # List of SKUs
    existing_variants = List(String()) # List of SKUs

class ProductSchema(FieldPermissionMixin, ProductBaseSchema):
    id = Integer(dump_only=True)
    category_name = String(attribute='category.name', dump_only=True)
    
    # Nested Data
    variants = List(Nested(ProductVariantSchema))
    reference_codes = List(Nested(ProductReferenceCodeSchema))
    
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)

class ProductOutSchema(ProductSchema):
    pass
