"""发货单采购明细Schema"""
from apiflask import Schema
from apiflask.fields import String, Integer, Float, Date
from marshmallow import validates, ValidationError


class ShipmentPurchaseItemSchema(Schema):
    """采购明细输出Schema"""
    id = Integer(dump_only=True)
    shipment_order_id = Integer(dump_only=True)
    
    # 采购订单信息
    purchase_order_id = Integer(
        allow_none=True,
        metadata={
            'description': '采购订单ID',
            'example': 123
        }
    )
    purchase_order_no = String(
        allow_none=True,
        metadata={
            'description': '采购订单号',
            'example': 'PO-2025-001'
        }
    )
    purchase_line_id = Integer(
        allow_none=True,
        metadata={
            'description': '采购订单行ID',
            'example': 456
        }
    )
    
    # 商品信息
    product_variant_id = Integer(
        required=True,
        metadata={
            'description': '商品变体ID',
            'example': 789
        }
    )
    sku = String(
        required=True,
        metadata={
            'description': '商品SKU',
            'example': 'A001-RED-M'
        }
    )
    product_name = String(
        required=True,
        metadata={
            'description': '商品名称',
            'example': '测试商品'
        }
    )
    
    # 数量
    quantity = Integer(
        required=True,
        metadata={
            'description': '发货数量',
            'example': 100
        }
    )
    unit = String(
        metadata={
            'description': '单位',
            'example': '件'
        }
    )
    
    # 价格信息（采购成本）
    purchase_unit_price = Float(
        required=True,
        metadata={
            'description': '采购单价',
            'example': 10.50
        }
    )
    purchase_total_price = Float(
        required=True,
        metadata={
            'description': '采购总价',
            'example': 1050.00
        }
    )
    purchase_currency = String(
        metadata={
            'description': '采购币种',
            'example': 'CNY'
        }
    )
    
    # 供应商信息
    supplier_id = Integer(
        allow_none=True,
        metadata={
            'description': '供应商ID',
            'example': 10
        }
    )
    supplier_name = String(
        allow_none=True,
        metadata={
            'description': '供应商名称',
            'example': '供应商A'
        }
    )
    
    # 批次信息
    batch_no = String(
        allow_none=True,
        metadata={
            'description': '采购批次号',
            'example': 'BATCH-2025-001'
        }
    )
    production_date = Date(
        allow_none=True,
        metadata={
            'description': '生产日期',
            'example': '2025-01-01'
        }
    )
    expire_date = Date(
        allow_none=True,
        metadata={
            'description': '过期日期',
            'example': '2026-01-01'
        }
    )
    
    # 仓库信息
    warehouse_id = Integer(
        allow_none=True,
        metadata={
            'description': '仓库ID',
            'example': 5
        }
    )
    warehouse_location = String(
        allow_none=True,
        metadata={
            'description': '仓库位置',
            'example': 'A-01-02'
        }
    )
    
    # 备注
    notes = String(
        allow_none=True,
        metadata={
            'description': '备注',
            'example': '备注信息'
        }
    )
    
    # 时间戳
    created_at = String(dump_only=True)
    updated_at = String(dump_only=True)
    created_by = Integer(dump_only=True)


class ShipmentPurchaseItemCreateSchema(Schema):
    """创建采购明细Schema"""
    
    # 采购订单信息（可选）
    purchase_order_id = Integer(
        allow_none=True,
        metadata={
            'description': '采购订单ID',
            'example': 123
        }
    )
    purchase_order_no = String(
        allow_none=True,
        metadata={
            'description': '采购订单号',
            'example': 'PO-2025-001'
        }
    )
    purchase_line_id = Integer(
        allow_none=True,
        metadata={
            'description': '采购订单行ID',
            'example': 456
        }
    )
    
    # 商品信息（至少提供product_variant_id或sku之一）
    product_variant_id = Integer(
        allow_none=True,
        metadata={
            'description': '商品变体ID（可选，如果不提供会通过SKU查找）',
            'example': 789
        }
    )
    sku = String(
        required=True,
        metadata={
            'description': '商品SKU',
            'example': 'A001-RED-M'
        }
    )
    product_name = String(
        required=True,
        metadata={
            'description': '商品名称',
            'example': '测试商品'
        }
    )
    
    # 数量（必填）
    quantity = Integer(
        required=True,
        metadata={
            'description': '发货数量',
            'example': 100
        }
    )
    unit = String(
        load_default='件',
        metadata={
            'description': '单位',
            'example': '件'
        }
    )
    
    # 价格信息（必填）
    purchase_unit_price = Float(
        required=True,
        metadata={
            'description': '采购单价',
            'example': 10.50
        }
    )
    purchase_currency = String(
        load_default='CNY',
        metadata={
            'description': '采购币种',
            'example': 'CNY'
        }
    )
    
    # 供应商信息（可选）
    supplier_id = Integer(
        allow_none=True,
        metadata={
            'description': '供应商ID',
            'example': 10
        }
    )
    supplier_name = String(
        allow_none=True,
        metadata={
            'description': '供应商名称',
            'example': '供应商A'
        }
    )
    
    # 批次信息（可选）
    batch_no = String(
        allow_none=True,
        metadata={
            'description': '采购批次号',
            'example': 'BATCH-2025-001'
        }
    )
    production_date = Date(
        allow_none=True,
        metadata={
            'description': '生产日期',
            'example': '2025-01-01'
        }
    )
    expire_date = Date(
        allow_none=True,
        metadata={
            'description': '过期日期',
            'example': '2026-01-01'
        }
    )
    
    # 仓库信息（可选）
    warehouse_id = Integer(
        allow_none=True,
        metadata={
            'description': '仓库ID',
            'example': 5
        }
    )
    warehouse_location = String(
        allow_none=True,
        metadata={
            'description': '仓库位置',
            'example': 'A-01-02'
        }
    )
    
    # 备注
    notes = String(
        allow_none=True,
        metadata={
            'description': '备注',
            'example': '备注信息'
        }
    )
    
    @validates('quantity')
    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError('数量必须大于0')
    
    @validates('purchase_unit_price')
    def validate_purchase_unit_price(self, value):
        if value <= 0:
            raise ValidationError('采购单价必须大于0')


class ShipmentPurchaseItemUpdateSchema(Schema):
    """更新采购明细Schema"""
    
    quantity = Integer(
        metadata={
            'description': '发货数量',
            'example': 100
        }
    )
    purchase_unit_price = Float(
        metadata={
            'description': '采购单价',
            'example': 10.50
        }
    )
    purchase_currency = String(
        metadata={
            'description': '采购币种',
            'example': 'CNY'
        }
    )
    supplier_id = Integer(
        allow_none=True,
        metadata={
            'description': '供应商ID',
            'example': 10
        }
    )
    supplier_name = String(
        allow_none=True,
        metadata={
            'description': '供应商名称',
            'example': '供应商A'
        }
    )
    batch_no = String(
        allow_none=True,
        metadata={
            'description': '采购批次号',
            'example': 'BATCH-2025-001'
        }
    )
    warehouse_location = String(
        allow_none=True,
        metadata={
            'description': '仓库位置',
            'example': 'A-01-02'
        }
    )
    notes = String(
        allow_none=True,
        metadata={
            'description': '备注'
        }
    )
    
    @validates('quantity')
    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError('数量必须大于0')
    
    @validates('purchase_unit_price')
    def validate_purchase_unit_price(self, value):
        if value <= 0:
            raise ValidationError('采购单价必须大于0')

