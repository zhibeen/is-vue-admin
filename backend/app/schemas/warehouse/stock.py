from apiflask import Schema
from apiflask.fields import String, Integer, Float, DateTime, Nested, Decimal
from apiflask.validators import Length, Range, OneOf
from marshmallow import validates_schema, ValidationError
from datetime import datetime


class StockSchema(Schema):
    """库存Schema"""
    id = Integer(dump_only=True)
    sku = String(
        required=True,
        metadata={
            'description': 'SKU编码',
            'example': 'SKU001'
        }
    )
    warehouse_id = Integer(required=True, metadata={'description': '仓库ID'})
    physical_quantity = Integer(metadata={'description': '物理库存'})
    available_quantity = Integer(metadata={'description': '可用库存'})
    allocated_quantity = Integer(metadata={'description': '已分配库存'})
    in_transit_quantity = Integer(metadata={'description': '在途库存'})
    damaged_quantity = Integer(metadata={'description': '坏品库存'})
    batch_no = String(metadata={'description': '批次号'})
    weight = Float(metadata={'description': '重量(kg)'})
    volume = Float(metadata={'description': '体积(m³)'})
    unit_cost = Decimal(metadata={'description': '单位成本'})
    currency = String(metadata={'description': '成本币种'})
    version = Integer(dump_only=True, metadata={'description': '版本号'})
    created_at = DateTime(dump_only=True, metadata={'description': '创建时间'})
    updated_at = DateTime(dump_only=True, metadata={'description': '更新时间'})


class StockQuerySchema(Schema):
    """库存查询Schema"""
    sku = String(metadata={'description': 'SKU编码'})
    warehouse_id = Integer(metadata={'description': '仓库ID'})
    batch_no = String(metadata={'description': '批次号'})
    min_quantity = Integer(metadata={'description': '最小库存量'})
    max_quantity = Integer(metadata={'description': '最大库存量'})


class StockAdjustSchema(Schema):
    """库存调整Schema"""
    sku = String(
        required=True,
        metadata={
            'description': 'SKU编码',
            'example': 'SKU001'
        }
    )
    warehouse_id = Integer(required=True, metadata={'description': '仓库ID'})
    quantity_delta = Integer(
        required=True,
        metadata={
            'description': '库存变化量（正数增加，负数减少）',
            'example': 100
        }
    )
    order_type = String(
        required=True,
        validate=OneOf(['inbound', 'outbound', 'transfer', 'adjustment']),
        metadata={
            'description': '单据类型',
            'example': 'inbound'
        }
    )
    order_no = String(
        required=True,
        metadata={
            'description': '单据编号',
            'example': 'IN202501010001'
        }
    )
    batch_no = String(metadata={'description': '批次号'})
    unit_cost = Decimal(metadata={'description': '单位成本'})
    currency = String(metadata={'description': '成本币种'})
    location_id = Integer(metadata={'description': '库位ID'})


class StockMovementSchema(Schema):
    """库存流水Schema"""
    id = Integer(dump_only=True)
    sku = String(metadata={'description': 'SKU编码'})
    warehouse_id = Integer(metadata={'description': '仓库ID'})
    location_id = Integer(metadata={'description': '库位ID'})
    order_type = String(metadata={'description': '单据类型'})
    order_no = String(metadata={'description': '单据编号'})
    biz_time = DateTime(metadata={'description': '业务时间'})
    quantity_delta = Integer(metadata={'description': '库存变化量'})
    batch_no = String(metadata={'description': '批次号'})
    unit_cost = Decimal(metadata={'description': '单位成本'})
    currency = String(metadata={'description': '成本币种'})
    exchange_rate = Decimal(metadata={'description': '汇率'})
    created_by = Integer(metadata={'description': '创建人ID'})
    created_at = DateTime(metadata={'description': '创建时间'})
    status = String(metadata={'description': '状态'})


class StockMovementQuerySchema(Schema):
    """库存流水查询Schema"""
    sku = String(metadata={'description': 'SKU编码'})
    warehouse_id = Integer(metadata={'description': '仓库ID'})
    order_type = String(metadata={'description': '单据类型'})
    order_no = String(metadata={'description': '单据编号'})
    start_date = DateTime(metadata={'description': '开始时间'})
    end_date = DateTime(metadata={'description': '结束时间'})


class StockDiscrepancySchema(Schema):
    """库存差异Schema"""
    id = Integer(dump_only=True)
    warehouse_id = Integer(metadata={'description': '仓库ID'})
    sku = String(metadata={'description': 'SKU编码'})
    local_qty = Integer(metadata={'description': '本地库存'})
    remote_qty = Integer(metadata={'description': '远程库存'})
    diff_ratio = Float(metadata={'description': '差异比例'})
    diff_amount = Decimal(metadata={'description': '差异金额'})
    status = String(metadata={'description': '状态'})
    discovered_at = DateTime(metadata={'description': '发现时间'})
    resolved_at = DateTime(metadata={'description': '解决时间'})
    resolver_id = Integer(metadata={'description': '解决人ID'})
    resolution = String(metadata={'description': '解决方案'})
    created_at = DateTime(metadata={'description': '创建时间'})
    updated_at = DateTime(metadata={'description': '更新时间'})


class StockDiscrepancyResolveSchema(Schema):
    """库存差异解决Schema"""
    resolution = String(
        required=True,
        validate=OneOf(['use_remote', 'use_local', 'ignore']),
        metadata={
            'description': '解决方案: use_remote(以第三方为准)/use_local(以本地为准)/ignore(忽略)',
            'example': 'use_remote'
        }
    )
    note = String(metadata={'description': '备注说明'})
