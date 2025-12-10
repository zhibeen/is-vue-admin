from apiflask import Schema
from apiflask.fields import Integer, String, List, Boolean, Nested, DateTime, Dict, Raw
from apiflask.validators import Regexp, OneOf
from marshmallow import pre_load, post_load

# 修正 AttributeDefinitionSchema 以匹配 Model
class AttributeDefinitionSchema(Schema):
    id = Integer()
    # Map model fields to schema fields
    # key_name -> key
    key = String(attribute='key_name') 
    # label -> label
    label = String(attribute='label')
    
    # NEW fields
    name_en = String(allow_none=True)
    description = String(allow_none=True)
    
    # data_type -> type
    type = String(attribute='data_type')
    
    # Options can be complex objects or strings. Using Raw to avoid validation errors on mixed content.
    # Frontend expects { label: string, value: any } or strings.
    options = Raw(allow_none=True)
    
    group_name = String(allow_none=True) # New field
    
    code_weight = Integer() # Added code_weight to schema as it's in model
    
    is_global = Boolean()
    allow_custom = Boolean() # New field

# 用于返回 CategoryAttribute 关联信息的 Schema
class CategoryAttributeMappingSchema(Schema):
    category_id = Integer()
    attribute_id = Integer()
    is_required = Boolean()
    display_order = Integer()
    include_in_code = Boolean(allow_none=True) # New override field
    options = Raw(allow_none=True, metadata={'description': 'Override global options if set'}) # New override field
    group_name = String(allow_none=True, metadata={'description': 'Override attribute group'}) # New override field
    attribute_scope = String(load_default='spu', validate=OneOf(['spu', 'sku']), metadata={'description': '属性作用域: spu/sku'}) # New field
    allow_custom = Boolean(allow_none=True, metadata={'description': 'Override allow_custom'}) # New override field


    # 包含完整属性定义
    attribute = Nested(AttributeDefinitionSchema, attribute='attribute_definition', allow_none=True)

class EffectiveAttributeSchema(AttributeDefinitionSchema):
    origin = String(metadata={'description': '来源类型', 'enum': ['self', 'inherited']})
    origin_category_id = Integer(allow_none=True)
    origin_category_name = String(allow_none=True)
    editable = Boolean(metadata={'description': '是否可编辑(inherited不可编辑)'})
    display_order = Integer(load_default=0)
    is_required = Boolean(load_default=False)
    include_in_code = Boolean(allow_none=True) # Override value
    group_name = String(allow_none=True) # Effective Group Name (Self > Global)
    attribute_scope = String(allow_none=True) # NEW
    override_options = Raw(allow_none=True, metadata={'description': 'Raw override options value (null if inheriting)'})
    effective_options = Raw(allow_none=True, metadata={'description': 'Calculated effective options (override or global)'})


class CategoryBaseSchema(Schema):
    name = String(required=True)
    name_en = String(required=False)
    code = String(
        required=True,
        # validate=Regexp(r'^[1-9]\d{2}$', error='SKU编码必须为3位数字且首位不能为0'),
        metadata={'description': 'SKU分类码(3位)', 'example': '101'}
    )
    abbreviation = String(
        validate=Regexp(r'^[A-Za-z0-9]+$', error='特征码只能包含字母和数字'), 
        metadata={'description': '业务特征码(用于生成SPU特征码)', 'example': 'HL'}
    )
    business_type = String(
        load_default='vehicle',
        metadata={'description': '业务线类型 (vehicle/general/electronics)', 'example': 'vehicle'}
    )
    spu_config = Dict(
        allow_none=True,
        metadata={'description': 'SPU表单配置与生成模板', 'example': {'template': '...', 'fields': ['...']}}
    )
    parent_id = Integer(allow_none=True)
    description = String()
    icon = String()
    is_active = Boolean(load_default=True)
    sort_order = Integer(load_default=0)
    is_leaf = Boolean(load_default=False) # 添加 is_leaf 字段

    @pre_load
    def format_english_name(self, data, **kwargs):
        if 'name_en' in data and data['name_en']:
            # Title Case: First letter of each word uppercase
            # Example: "tail light" -> "Tail Light"
            data['name_en'] = data['name_en'].strip().title()
        return data

    @post_load
    def normalize_spu_config(self, data, **kwargs):
        # 1. 业务线防呆：非汽配类目清除 vehicle_link
        if data.get('business_type') != 'vehicle':
            if 'spu_config' in data and data['spu_config'] and isinstance(data['spu_config'], dict) and 'vehicle_link' in data['spu_config']:
                del data['spu_config']['vehicle_link']
            return data

        # 2. 自动规范化 SPU Config 中的 vehicle_link 层级顺序 (仅针对 vehicle)
        if 'spu_config' in data and data['spu_config']:
            config = data['spu_config']
            if isinstance(config, dict) and 'vehicle_link' in config:
                v_link = config['vehicle_link']
                if v_link and isinstance(v_link, dict) and 'levels' in v_link:
                    levels = v_link['levels']
                    if isinstance(levels, list):
                        # 定义标准权重 (保持与 SysDict:vehicle_level_type 一致)
                        ORDER_MAP = {
                            'make': 10,
                            'series': 15,
                            'model': 20,
                            'year': 30,
                            'engine': 40,
                            'trim': 50
                        }
                        # 排序
                        v_link['levels'] = sorted(
                            levels, 
                            key=lambda x: ORDER_MAP.get(x, 999)
                        )
        return data

class CategoryDetailSchema(CategoryBaseSchema):
    id = Integer()
    # path = String() # Not in model yet, optional
    level = Integer()
    created_at = DateTime()
    updated_at = DateTime() # Not in model, remove if not needed or add to model
    effective_spu_config = Dict(dump_only=True) # 只读字段，返回计算后的配置


class CategoryTreeSchema(CategoryDetailSchema):
    children = List(Nested(lambda: CategoryTreeSchema()))
    
    @pre_load
    def sort_children(self, data, **kwargs):
        # Marshmallow pre_load works on input data, usually dicts.
        # But here we are serializing model objects (dump). 
        # Marshmallow does not have a built-in pre_dump hook for list sorting easily without custom field.
        # So sorting children is better handled in the model or view.
        pass
        
    # Better approach: Sort children in the model relationship or using a Method field.
    # Since we are using SQLAlchemy, we can add order_by to the relationship in the model.
    # Or we can sort in python after fetching. 
    # Let's rely on model relationship ordering if possible, or python sorting.

