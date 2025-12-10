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
    
    # Pack Dimensions
    pack_length = DecimalField()
    pack_width = DecimalField()
    pack_height = DecimalField()
    
    # Net Weight (Separate from weight which might be gross)
    net_weight = DecimalField()
    
    created_at = DateTime(dump_only=True)

# --- SKU List & Detail Schemas ---

class SkuListItemSchema(Schema):
    """SKU列表项Schema"""
    sku = String(metadata={'description': 'SKU编码'})
    feature_code = String(metadata={'description': '特征码'})
    product_id = Integer(metadata={'description': '产品ID'})
    product_name = String(metadata={'description': '产品名称'})
    spu_code = String(metadata={'description': 'SPU编码'})
    category_id = Integer(metadata={'description': '分类ID'})
    category_name = String(metadata={'description': '分类名称'})
    brand = String(metadata={'description': '品牌'})
    model = String(metadata={'description': '车型'})
    attributes_display = String(metadata={'description': '属性组合显示'})
    stock_quantity = Integer(metadata={'description': '当前库存'})
    safety_stock = Integer(metadata={'description': '安全库存'})
    in_transit = Integer(metadata={'description': '在途数量'})
    warning_status = String(metadata={'description': '预警状态: normal/warning/danger'})
    quality_type = String(metadata={'description': '质量类型: Aftermarket/OEM/Refurbished'})
    is_active = Boolean(metadata={'description': '是否启用'})
    created_at = DateTime(metadata={'description': '创建时间'})
    updated_at = DateTime(metadata={'description': '更新时间'})

class SkuListResponseSchema(Schema):
    """SKU列表响应Schema"""
    items = List(Nested(SkuListItemSchema))
    total = Integer()
    page = Integer()
    per_page = Integer()
    pages = Integer()

class SkuCodingRulesSchema(Schema):
    """SKU编码规则Schema"""
    category_code = String(metadata={'description': '类目码(3位)'})
    vehicle_code = String(metadata={'description': '车型码(4位)'})
    brand_code = String(metadata={'description': '品牌码(2位)'})
    model_code = String(metadata={'description': '车型码(2位)'})
    serial = String(metadata={'description': '流水号(2位)'})
    suffix = String(metadata={'description': '属性后缀'})
    category_abbreviation = String(metadata={'description': '类目缩写'})
    category_code_db = String(metadata={'description': '数据库中的类目码'})

class SkuComplianceInfoSchema(Schema):
    """SKU合规信息Schema"""
    hs_code = String(metadata={'description': 'HS编码'})
    declared_name = String(metadata={'description': '申报品名'})
    declared_unit = String(metadata={'description': '申报单位'})
    net_weight = DecimalField(metadata={'description': '净重(KG)'})
    gross_weight = DecimalField(metadata={'description': '毛重(KG)'})
    package_dimensions = String(metadata={'description': '包装尺寸'})

class SkuReferenceCodeSchema(Schema):
    """SKU参考编码Schema"""
    code = String(metadata={'description': '参考编码'})
    code_type = String(metadata={'description': '编码类型: OE/OEM/PARTSLINK'})
    brand = String(metadata={'description': '品牌'})

class SkuFitmentSchema(Schema):
    """SKU适配车型Schema"""
    make = String(metadata={'description': '品牌'})
    model = String(metadata={'description': '车型'})
    sub_model = String(metadata={'description': '子车型'})
    year_start = Integer(metadata={'description': '起始年份'})
    year_end = Integer(metadata={'description': '结束年份'})
    position = String(metadata={'description': '安装位置'})

class SkuDetailSchema(Schema):
    """SKU详情Schema"""
    sku = String(metadata={'description': 'SKU编码'})
    feature_code = String(metadata={'description': '特征码'})
    product_id = Integer(metadata={'description': '产品ID'})
    product_name = String(metadata={'description': '产品名称'})
    spu_code = String(metadata={'description': 'SPU编码'})
    category_id = Integer(metadata={'description': '分类ID'})
    category_name = String(metadata={'description': '分类名称'})
    brand = String(metadata={'description': '品牌'})
    model = String(metadata={'description': '车型'})
    attributes = Dict(metadata={'description': '属性详情'})
    attributes_display = String(metadata={'description': '属性组合显示'})
    compliance_info = Nested(SkuComplianceInfoSchema, metadata={'description': '合规信息'})
    coding_rules = Nested(SkuCodingRulesSchema, metadata={'description': '编码规则'})
    reference_codes = List(Nested(SkuReferenceCodeSchema), metadata={'description': '参考编码'})
    fitments = List(Nested(SkuFitmentSchema), metadata={'description': '适配车型'})
    stock_quantity = Integer(metadata={'description': '当前库存'})
    safety_stock = Integer(metadata={'description': '安全库存'})
    in_transit = Integer(metadata={'description': '在途数量'})
    warning_status = String(metadata={'description': '预警状态: normal/warning/danger'})
    quality_type = String(metadata={'description': '质量类型: Aftermarket/OEM/Refurbished'})
    is_active = Boolean(metadata={'description': '是否启用'})
    created_at = DateTime(metadata={'description': '创建时间'})
    updated_at = DateTime(metadata={'description': '更新时间'})

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
    is_active = Boolean(dump_only=True)  # Added field
    
    # Nested Data
    variants = List(Nested(ProductVariantSchema))
    reference_codes = List(Nested(ProductReferenceCodeSchema))
    
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)

class ProductOutSchema(ProductSchema):
    pass
