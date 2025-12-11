from apiflask import Schema
from apiflask.fields import String, Integer, Float, Boolean, DateTime, Nested, List, Dict, Decimal
from apiflask.validators import Length, Range, OneOf
from marshmallow import validates_schema, ValidationError


class WarehouseStatsSchema(Schema):
    """仓库统计Schema"""
    total = Integer(metadata={'description': '总仓库数'})
    physical = Integer(metadata={'description': '实体仓数量'})
    virtual = Integer(metadata={'description': '虚拟仓数量'})
    domestic = Integer(metadata={'description': '国内仓数量'})
    overseas = Integer(metadata={'description': '海外仓数量'})
    active = Integer(metadata={'description': '正常运营数量'})


class WarehouseQuerySchema(Schema):
    """仓库查询Schema - 支持多值筛选（逗号分隔）"""
    page = Integer(load_default=1, metadata={'description': '页码'})
    per_page = Integer(load_default=20, metadata={'description': '每页数量'})
    q = String(load_default=None, metadata={'description': '搜索关键词（编码或名称）'})
    keyword = String(load_default=None, metadata={'description': '搜索关键词（兼容前端参数名）'})
    
    # 支持多值筛选：可传单个值或逗号分隔的多个值，如 "physical" 或 "physical,virtual"
    category = String(
        load_default=None,
        metadata={
            'description': '仓库形态: physical/virtual，支持多选（逗号分隔）',
            'example': 'physical,virtual'
        }
    )
    location_type = String(
        load_default=None,
        metadata={
            'description': '地理位置: domestic/overseas，支持多选（逗号分隔）',
            'example': 'domestic,overseas'
        }
    )
    ownership_type = String(
        load_default=None,
        metadata={
            'description': '权属类型: self/third_party，支持多选（逗号分隔）',
            'example': 'self,third_party'
        }
    )
    status = String(
        load_default=None,
        metadata={
            'description': '仓库状态，支持多选（逗号分隔）',
            'example': 'active,planning'
        }
    )


class WarehouseSchema(Schema):
    """仓库基础Schema (v1.3 Updated)"""
    id = Integer(dump_only=True)
    code = String(
        required=True,
        metadata={'description': '仓库编码', 'example': 'WH001'}
    )
    name = String(
        required=True,
        metadata={'description': '仓库名称', 'example': '深圳总仓'}
    )
    category = String(
        validate=OneOf(['physical', 'virtual']),
        load_default='physical',
        metadata={'description': '形态: physical/virtual', 'example': 'physical'}
    )
    location_type = String(
        validate=OneOf(['domestic', 'overseas']),
        load_default='domestic',
        metadata={'description': '地理: domestic/overseas', 'example': 'domestic'}
    )
    ownership_type = String(
        validate=OneOf(['self', 'third_party']),
        load_default='self',
        metadata={'description': '权属: self/third_party', 'example': 'self'}
    )
    status = String(
        validate=OneOf(['planning', 'active', 'suspended', 'clearing', 'deprecated']),
        load_default='active',
        metadata={'description': '状态', 'example': 'active'}
    )
    business_type = String(
        load_default='standard',
        metadata={'description': '业务类型(bonded/fba/standard)', 'example': 'standard'}
    )
    currency = String(
        load_default='USD',
        metadata={'description': '计价币种', 'example': 'USD'}
    )
    # api_config 仅存映射关系，不含敏感认证
    api_config = Dict(
        allow_none=True,
        metadata={'description': '第三方映射配置', 'example': {'external_code': 'US01'}}
    )
    child_warehouse_ids = List(Integer(), metadata={'description': '子仓ID列表(仅虚拟总仓)'})
    
    capacity = Float(metadata={'description': '容量'})
    max_volume = Float(metadata={'description': '最大体积(m3)'})
    timezone = String(load_default='UTC')
    
    contact_person = String()
    contact_phone = String()
    contact_email = String()
    address = String()
    
    # 第三方关联字段
    third_party_service_id = Integer(allow_none=True, metadata={'description': '第三方服务商ID'})
    third_party_warehouse_id = Integer(allow_none=True, metadata={'description': '第三方仓库ID'})
    
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)


class WarehouseCreateSchema(WarehouseSchema):
    """创建仓库Schema"""
    pass


class WarehouseUpdateSchema(Schema):
    """更新仓库Schema"""
    name = String()
    status = String(validate=OneOf(['planning', 'active', 'suspended', 'clearing', 'deprecated']))
    business_type = String()
    currency = String()
    api_config = Dict(allow_none=True)
    child_warehouse_ids = List(Integer())
    capacity = Float(allow_none=True)
    max_volume = Float(allow_none=True)
    timezone = String()
    contact_person = String()
    contact_phone = String()
    contact_email = String()
    address = String()
    # 添加第三方关联字段
    third_party_service_id = Integer(allow_none=True, metadata={'description': '第三方服务商ID'})
    third_party_warehouse_id = Integer(allow_none=True, metadata={'description': '第三方仓库ID'})


class WarehouseLocationSchema(Schema):
    """库位Schema"""
    id = Integer(dump_only=True)
    warehouse_id = Integer(dump_only=True)
    code = String(required=True)
    type = String(load_default='storage')
    is_locked = Boolean(load_default=False)
    allow_mixing = Boolean(load_default=False)


class WarehouseLocationCreateSchema(WarehouseLocationSchema):
    pass


class WarehouseLocationUpdateSchema(Schema):
    is_locked = Boolean()
    allow_mixing = Boolean()
    type = String()
