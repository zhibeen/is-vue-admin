from apiflask import Schema
from apiflask.fields import String, Integer, Float, DateTime, Nested, List
from apiflask.validators import Length, Range, OneOf
from marshmallow import validates_schema, ValidationError
from datetime import datetime


class WarehouseProductGroupSchema(Schema):
    """SKU分组Schema"""
    id = Integer(dump_only=True)
    code = String(
        required=True,
        metadata={
            'description': '分组编码',
            'example': 'GROUP001'
        }
    )
    name = String(
        required=True,
        metadata={
            'description': '分组名称',
            'example': '2025黑五促销组'
        }
    )
    note = String(metadata={'description': '备注'})
    created_by = Integer(dump_only=True, metadata={'description': '创建人ID'})
    created_at = DateTime(dump_only=True, metadata={'description': '创建时间'})
    updated_at = DateTime(dump_only=True, metadata={'description': '更新时间'})


class WarehouseProductGroupCreateSchema(Schema):
    """创建SKU分组Schema"""
    code = String(
        required=True,
        validate=Length(min=1, max=50),
        metadata={
            'description': '分组编码',
            'example': 'GROUP001'
        }
    )
    name = String(
        required=True,
        validate=Length(min=1, max=100),
        metadata={
            'description': '分组名称',
            'example': '2025黑五促销组'
        }
    )
    note = String(metadata={'description': '备注'})


class WarehouseProductGroupItemSchema(Schema):
    """SKU分组明细Schema"""
    group_id = Integer(required=True, metadata={'description': '分组ID'})
    sku = String(
        required=True,
        metadata={
            'description': 'SKU编码',
            'example': 'SKU001'
        }
    )
    created_at = DateTime(dump_only=True, metadata={'description': '创建时间'})


class WarehouseProductGroupItemCreateSchema(Schema):
    """创建SKU分组明细Schema"""
    sku = String(
        required=True,
        metadata={
            'description': 'SKU编码',
            'example': 'SKU001'
        }
    )


class StockAllocationPolicySchema(Schema):
    """库存分配策略Schema"""
    id = Integer(dump_only=True)
    virtual_warehouse_id = Integer(required=True, metadata={'description': '虚拟仓ID'})
    source_warehouse_id = Integer(metadata={'description': '源仓库ID'})
    category_id = Integer(metadata={'description': '品类ID'})
    warehouse_product_group_id = Integer(metadata={'description': 'SKU分组ID'})
    sku = String(metadata={'description': 'SKU编码'})
    ratio = Float(
        validate=Range(min=0, max=1),
        metadata={
            'description': '分配比例(0-1)',
            'example': 0.8
        }
    )
    fixed_amount = Integer(metadata={'description': '固定分配量'})
    priority = Integer(metadata={'description': '优先级'})
    policy_mode = String(
        validate=OneOf(['override', 'inherit']),
        metadata={
            'description': '策略模式: override(覆盖)/inherit(继承)',
            'example': 'override'
        }
    )
    effective_from = DateTime(metadata={'description': '生效开始时间'})
    effective_to = DateTime(metadata={'description': '生效结束时间'})
    created_by = Integer(dump_only=True, metadata={'description': '创建人ID'})
    created_at = DateTime(dump_only=True, metadata={'description': '创建时间'})
    updated_at = DateTime(dump_only=True, metadata={'description': '更新时间'})
    
    @validates_schema
    def validate_allocation(self, data, **kwargs):
        """验证分配策略"""
        ratio = data.get('ratio')
        fixed_amount = data.get('fixed_amount')
        
        if ratio is None and fixed_amount is None:
            raise ValidationError('必须指定分配比例或固定分配量')
        
        if ratio is not None and fixed_amount is not None:
            raise ValidationError('不能同时指定分配比例和固定分配量')


class StockAllocationPolicyCreateSchema(Schema):
    """创建库存分配策略Schema"""
    virtual_warehouse_id = Integer(required=True, metadata={'description': '虚拟仓ID'})
    source_warehouse_id = Integer(metadata={'description': '源仓库ID'})
    category_id = Integer(metadata={'description': '品类ID'})
    warehouse_product_group_id = Integer(metadata={'description': 'SKU分组ID'})
    sku = String(metadata={'description': 'SKU编码'})
    ratio = Float(
        validate=Range(min=0, max=1),
        metadata={
            'description': '分配比例(0-1)',
            'example': 0.8
        }
    )
    fixed_amount = Integer(metadata={'description': '固定分配量'})
    priority = Integer(metadata={'description': '优先级'})
    policy_mode = String(
        validate=OneOf(['override', 'inherit']),
        metadata={
            'description': '策略模式',
            'example': 'override'
        }
    )
    effective_from = DateTime(metadata={'description': '生效开始时间'})
    effective_to = DateTime(metadata={'description': '生效结束时间'})
    
    @validates_schema
    def validate_allocation(self, data, **kwargs):
        """验证分配策略"""
        ratio = data.get('ratio')
        fixed_amount = data.get('fixed_amount')
        
        if ratio is None and fixed_amount is None:
            raise ValidationError('必须指定分配比例或固定分配量')
        
        if ratio is not None and fixed_amount is not None:
            raise ValidationError('不能同时指定分配比例和固定分配量')


class StockAllocationPolicyUpdateSchema(Schema):
    """更新库存分配策略Schema"""
    ratio = Float(
        validate=Range(min=0, max=1),
        metadata={
            'description': '分配比例(0-1)',
            'example': 0.8
        }
    )
    fixed_amount = Integer(metadata={'description': '固定分配量'})
    priority = Integer(metadata={'description': '优先级'})
    policy_mode = String(
        validate=OneOf(['override', 'inherit']),
        metadata={
            'description': '策略模式',
            'example': 'override'
        }
    )
    effective_from = DateTime(metadata={'description': '生效开始时间'})
    effective_to = DateTime(metadata={'description': '生效结束时间'})
