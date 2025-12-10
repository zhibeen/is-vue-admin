from apiflask import Schema
from apiflask.fields import String, Integer, Float, Boolean, DateTime, Nested, List, Dict, Decimal
from apiflask.validators import Length, Range, OneOf
from marshmallow import validates_schema, ValidationError
from datetime import datetime


class WarehouseSchema(Schema):
    """仓库基础Schema"""
    id = Integer(dump_only=True)
    code = String(
        required=True,
        metadata={
            'description': '仓库编码',
            'example': 'WH001'
        }
    )
    name = String(
        required=True,
        metadata={
            'description': '仓库名称',
            'example': '深圳总仓'
        }
    )
    category = String(
        required=True,
        validate=OneOf(['physical', 'virtual']),
        metadata={
            'description': '仓库形态: physical(实体仓)/virtual(虚拟仓)',
            'example': 'physical'
        }
    )
    location_type = String(
        required=True,
        validate=OneOf(['domestic', 'overseas']),
        metadata={
            'description': '地理位置: domestic(国内)/overseas(海外)',
            'example': 'domestic'
        }
    )
    ownership_type = String(
        required=True,
        validate=OneOf(['self', 'third_party']),
        metadata={
            'description': '管理模式: self(自营)/third_party(三方)',
            'example': 'self'
        }
    )
    status = String(
        validate=OneOf(['planning', 'active', 'suspended', 'clearing', 'deprecated']),
        metadata={
            'description': '仓库状态',
            'example': 'active'
        }
    )
    business_type = String(
        metadata={
            'description': '业务标签',
            'example': 'standard'
        }
    )
    currency = String(
        metadata={
            'description': '计价币种',
            'example': 'USD'
        }
    )
    api_config = Dict(
        metadata={
            'description': '第三方API配置',
            'example': {'service_provider_id': 1, 'external_code': 'US-WEST-01'}
        }
    )
    child_warehouse_ids = List(Integer, metadata={'description': '虚拟仓子仓ID列表'})
    capacity = Float(metadata={'description': '仓库容量'})
    max_volume = Float(metadata={'description': '最大体积容量(m³)'})
    timezone = String(metadata={'description': '时区', 'example': 'Asia/Shanghai'})
    contact_person = String(metadata={'description': '联系人'})
    contact_phone = String(metadata={'description': '联系电话'})
    contact_email = String(metadata={'description': '联系邮箱'})
    address = String(metadata={'description': '地址'})
    created_by = Integer(dump_only=True, metadata={'description': '创建人ID'})
    created_at = DateTime(dump_only=True, metadata={'description': '创建时间'})
    updated_at = DateTime(dump_only=True, metadata={'description': '更新时间'})


class WarehouseCreateSchema(Schema):
    """创建仓库Schema"""
    code = String(
        required=True,
        validate=Length(min=1, max=50),
        metadata={
            'description': '仓库编码',
            'example': 'WH001'
        }
    )
    name = String(
        required=True,
        validate=Length(min=1, max=100),
        metadata={
            'description': '仓库名称',
            'example': '深圳总仓'
        }
    )
    category = String(
        required=True,
        validate=OneOf(['physical', 'virtual']),
        metadata={
            'description': '仓库形态',
            'example': 'physical'
        }
    )
    location_type = String(
        required=True,
        validate=OneOf(['domestic', 'overseas']),
        metadata={
            'description': '地理位置',
            'example': 'domestic'
        }
    )
    ownership_type = String(
        required=True,
        validate=OneOf(['self', 'third_party']),
        metadata={
            'description': '管理模式',
            'example': 'self'
        }
    )
    business_type = String(
        metadata={
            'description': '业务标签',
            'example': 'standard'
        }
    )
    currency = String(
        metadata={
            'description': '计价币种',
            'example': 'USD'
        }
    )
    capacity = Float(metadata={'description': '仓库容量'})
    max_volume = Float(metadata={'description': '最大体积容量(m³)'})
    contact_person = String(metadata={'description': '联系人'})
    contact_phone = String(metadata={'description': '联系电话'})
    contact_email = String(metadata={'description': '联系邮箱'})
    address = String(metadata={'description': '地址'})


class WarehouseUpdateSchema(Schema):
    """更新仓库Schema"""
    name = String(
        validate=Length(min=1, max=100),
        metadata={
            'description': '仓库名称',
            'example': '深圳总仓'
        }
    )
    status = String(
        validate=OneOf(['planning', 'active', 'suspended', 'clearing', 'deprecated']),
        metadata={
            'description': '仓库状态',
            'example': 'active'
        }
    )
    business_type = String(
        metadata={
            'description': '业务标签',
            'example': 'standard'
        }
    )
    currency = String(
        metadata={
            'description': '计价币种',
            'example': 'USD'
        }
    )
    api_config = Dict(
        metadata={
            'description': '第三方API配置'
        }
    )
    child_warehouse_ids = List(Integer, metadata={'description': '虚拟仓子仓ID列表'})
    capacity = Float(metadata={'description': '仓库容量'})
    max_volume = Float(metadata={'description': '最大体积容量(m³)'})
    contact_person = String(metadata={'description': '联系人'})
    contact_phone = String(metadata={'description': '联系电话'})
    contact_email = String(metadata={'description': '联系邮箱'})
    address = String(metadata={'description': '地址'})


class WarehouseLocationSchema(Schema):
    """库位Schema"""
    id = Integer(dump_only=True)
    warehouse_id = Integer(required=True, metadata={'description': '仓库ID'})
    code = String(
        required=True,
        metadata={
            'description': '库位编码',
            'example': 'A-01-01-01'
        }
    )
    type = String(
        validate=OneOf(['storage', 'pick', 'receive', 'return', 'stage']),
        metadata={
            'description': '库位类型',
            'example': 'storage'
        }
    )
    is_locked = Boolean(metadata={'description': '是否锁定'})
    allow_mixing = Boolean(metadata={'description': '是否允许混放'})
    max_quantity = Integer(metadata={'description': '最大数量'})
    max_weight = Float(metadata={'description': '最大重量(kg)'})
    max_volume = Float(metadata={'description': '最大体积(m³)'})
    status = String(
        validate=OneOf(['available', 'occupied', 'locked', 'maintenance']),
        metadata={
            'description': '库位状态',
            'example': 'available'
        }
    )
    created_by = Integer(dump_only=True, metadata={'description': '创建人ID'})
    created_at = DateTime(dump_only=True, metadata={'description': '创建时间'})
    updated_at = DateTime(dump_only=True, metadata={'description': '更新时间'})


class WarehouseLocationCreateSchema(Schema):
    """创建库位Schema"""
    warehouse_id = Integer(required=True, metadata={'description': '仓库ID'})
    code = String(
        required=True,
        validate=Length(min=1, max=50),
        metadata={
            'description': '库位编码',
            'example': 'A-01-01-01'
        }
    )
    type = String(
        validate=OneOf(['storage', 'pick', 'receive', 'return', 'stage']),
        metadata={
            'description': '库位类型',
            'example': 'storage'
        }
    )
    max_quantity = Integer(metadata={'description': '最大数量'})
    max_weight = Float(metadata={'description': '最大重量(kg)'})
    max_volume = Float(metadata={'description': '最大体积(m³)'})


class WarehouseLocationUpdateSchema(Schema):
    """更新库位Schema"""
    code = String(
        validate=Length(min=1, max=50),
        metadata={
            'description': '库位编码',
            'example': 'A-01-01-01'
        }
    )
    type = String(
        validate=OneOf(['storage', 'pick', 'receive', 'return', 'stage']),
        metadata={
            'description': '库位类型',
            'example': 'storage'
        }
    )
    is_locked = Boolean(metadata={'description': '是否锁定'})
    allow_mixing = Boolean(metadata={'description': '是否允许混放'})
    max_quantity = Integer(metadata={'description': '最大数量'})
    max_weight = Float(metadata={'description': '最大重量(kg)'})
    max_volume = Float(metadata={'description': '最大体积(m³)'})
    status = String(
        validate=OneOf(['available', 'occupied', 'locked', 'maintenance']),
        metadata={
            'description': '库位状态',
            'example': 'available'
        }
    )
