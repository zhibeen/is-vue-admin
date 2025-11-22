from apiflask import Schema
from apiflask.fields import String, Integer, List, Nested
from apiflask.validators import Length, Regexp

class VehicleAuxBaseSchema(Schema):
    name = String(
        required=True, 
        validate=Length(min=1, max=100),
        metadata={'description': '名称 (品牌/车型/车系)', 'example': '奥迪'}
    )

class BrandCreateSchema(VehicleAuxBaseSchema):
    code = String(
        required=True, 
        validate=[Length(equal=2), Regexp(r'^\d{2}$')],
        metadata={'description': '品牌编码 (2位数字)', 'example': '01'}
    )
    abbr = String(
        required=True, 
        validate=Length(min=1, max=10),
        metadata={'description': '品牌缩写 (用于快速检索)', 'example': 'AD'}
    )

class BrandUpdateSchema(VehicleAuxBaseSchema):
    code = String(
        validate=[Length(equal=2), Regexp(r'^\d{2}$')],
        metadata={'description': '品牌编码 (2位数字)', 'example': '01'}
    )
    abbr = String(
        validate=Length(min=1, max=10),
        metadata={'description': '品牌缩写', 'example': 'AD'}
    )

class ModelCreateSchema(VehicleAuxBaseSchema):
    brand_id = Integer(
        required=True,
        metadata={'description': '所属品牌ID', 'example': 1}
    )
    # name 字段继承自 VehicleAuxBaseSchema，示例为 'A4L'

class SubmodelCreateSchema(VehicleAuxBaseSchema):
    model_id = Integer(
        required=True,
        metadata={'description': '所属车型ID', 'example': 10}
    )
    # name 字段继承自 VehicleAuxBaseSchema，示例为 '2023款 40 TFSI 时尚动感型'

class VehicleAuxOutSchema(Schema):
    id = Integer(metadata={'description': 'ID'})
    name = String(metadata={'description': '名称'})
    level_type = String(metadata={'description': '层级类型 (brand/model/submodel)', 'example': 'brand'})
    
class BrandOutSchema(VehicleAuxOutSchema):
    code = String(metadata={'description': '品牌编码'})
    abbr = String(metadata={'description': '品牌缩写'})

class ModelOutSchema(VehicleAuxOutSchema):
    brand_id = Integer(attribute='parent_id', metadata={'description': '所属品牌ID'})

class SubmodelOutSchema(VehicleAuxOutSchema):
    model_id = Integer(attribute='parent_id', metadata={'description': '所属车型ID'})

