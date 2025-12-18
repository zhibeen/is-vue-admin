"""发货单相关Schemas"""
from apiflask import Schema
from apiflask.fields import String, Integer, Float, Date, DateTime, Nested, List as ListField
from marshmallow import validates, ValidationError


class ShipmentOrderItemSchema(Schema):
    """发货单明细Schema"""
    id = Integer(dump_only=True)
    shipment_id = Integer(dump_only=True)
    
    # 产品信息
    product_id = Integer(metadata={'description': '产品ID'})
    sku = String(required=True, metadata={'description': 'SKU', 'example': 'P001'})
    product_name = String(required=True, metadata={'description': '商品名称'})
    product_name_en = String(metadata={'description': '英文品名'})
    
    # 归类信息
    hs_code = String(metadata={'description': 'HS编码'})
    customs_product_id = Integer(metadata={'description': '归类商品ID'})
    
    # 数量信息
    quantity = Float(required=True, metadata={'description': '数量'})
    unit = String(metadata={'description': '单位', 'example': 'PCS'})
    
    # 价格信息
    unit_price = Float(metadata={'description': '单价'})
    total_price = Float(metadata={'description': '总价'})
    
    # 重量信息
    unit_weight = Float(metadata={'description': '单件重量(kg)'})
    total_weight = Float(metadata={'description': '总重量(kg)'})
    
    # 原产地
    origin_country = String(metadata={'description': '原产国'})
    
    # 外部系统信息
    external_item_id = String(metadata={'description': '外部商品ID'})
    
    # 供应商信息（用于自动拆分生成交付合同）
    supplier_id = Integer(metadata={'description': '供应商ID'})


class ShipmentOrderSchema(Schema):
    """发货单Schema（输出）"""
    id = Integer(dump_only=True)
    shipment_no = String(dump_only=True, metadata={'description': '发货单号'})
    source = String(metadata={'description': '来源: manual/excel/lingxing/yicang'})
    status = String(metadata={'description': '状态'})
    
    # 外部系统数据
    external_order_no = String(metadata={'description': '外部订单号'})
    external_tracking_no = String(metadata={'description': '外部跟踪号'})
    
    # 基本信息
    shipper_company_id = Integer(required=True, metadata={'description': '发货公司ID'})
    consignee_id = Integer(metadata={'description': '境外收货人ID'})
    consignee_name = String(metadata={'description': '收货人名称'})
    consignee_address = String(metadata={'description': '收货地址'})
    consignee_country = String(metadata={'description': '收货国家'})
    
    # 物流信息
    logistics_provider = String(metadata={'description': '物流商'})
    tracking_no = String(metadata={'description': '物流跟踪号'})
    shipping_method = String(metadata={'description': '运输方式'})
    estimated_ship_date = Date(metadata={'description': '预计发货日期'})
    actual_ship_date = Date(metadata={'description': '实际发货日期'})
    
    # 包装信息
    total_packages = Integer(metadata={'description': '总件数'})
    total_gross_weight = Float(metadata={'description': '总毛重(kg)'})
    total_net_weight = Float(metadata={'description': '总净重(kg)'})
    total_volume = Float(metadata={'description': '总体积(m³)'})
    
    # 金额信息
    currency = String(metadata={'description': '币种', 'example': 'USD'})
    total_amount = Float(metadata={'description': '总金额'})
    
    # 关联状态
    customs_declaration_id = Integer(dump_only=True, metadata={'description': '关联报关单ID'})
    is_declared = Integer(dump_only=True, metadata={'description': '是否已生成报关单'})
    is_contracted = Integer(dump_only=True, metadata={'description': '是否已生成交付合同'})
    
    # 备注
    notes = String(metadata={'description': '备注'})
    
    # 审计字段
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)
    created_by = Integer(dump_only=True)
    
    # 明细
    items = ListField(Nested(ShipmentOrderItemSchema), metadata={'description': '发货明细'})


class ShipmentOrderCreateSchema(Schema):
    """发货单创建Schema"""
    source = String(metadata={'description': '来源', 'example': 'manual'})
    
    # 外部系统数据
    external_order_no = String(metadata={'description': '外部订单号'})
    external_tracking_no = String(metadata={'description': '外部跟踪号'})
    
    # 基本信息
    shipper_company_id = Integer(required=True, metadata={'description': '发货公司ID'})
    consignee_id = Integer(metadata={'description': '境外收货人ID'})
    consignee_name = String(metadata={'description': '收货人名称'})
    consignee_address = String(metadata={'description': '收货地址'})
    consignee_country = String(metadata={'description': '收货国家'})
    
    # 物流信息
    logistics_provider = String(metadata={'description': '物流商'})
    tracking_no = String(metadata={'description': '物流跟踪号'})
    shipping_method = String(metadata={'description': '运输方式'})
    estimated_ship_date = Date(metadata={'description': '预计发货日期'})
    
    # 包装信息
    total_packages = Integer(metadata={'description': '总件数'})
    total_gross_weight = Float(metadata={'description': '总毛重(kg)'})
    total_net_weight = Float(metadata={'description': '总净重(kg)'})
    total_volume = Float(metadata={'description': '总体积(m³)'})
    
    # 金额信息
    currency = String(metadata={'description': '币种', 'example': 'USD'})
    total_amount = Float(metadata={'description': '总金额'})
    
    # 备注
    notes = String(metadata={'description': '备注'})
    
    # 明细（必填）
    items = ListField(
        Nested(ShipmentOrderItemSchema),
        required=True,
        metadata={'description': '发货明细列表'}
    )
    
    @validates('items')
    def validate_items(self, value):
        if not value:
            raise ValidationError('发货明细不能为空')
        if len(value) == 0:
            raise ValidationError('至少需要一条发货明细')


class ShipmentOrderUpdateSchema(Schema):
    """发货单更新Schema"""
    status = String(metadata={'description': '状态'})
    
    # 物流信息
    logistics_provider = String(metadata={'description': '物流商'})
    tracking_no = String(metadata={'description': '物流跟踪号'})
    shipping_method = String(metadata={'description': '运输方式'})
    estimated_ship_date = Date(metadata={'description': '预计发货日期'})
    actual_ship_date = Date(metadata={'description': '实际发货日期'})
    
    # 包装信息
    total_packages = Integer(metadata={'description': '总件数'})
    total_gross_weight = Float(metadata={'description': '总毛重(kg)'})
    total_net_weight = Float(metadata={'description': '总净重(kg)'})
    total_volume = Float(metadata={'description': '总体积(m³)'})
    
    # 备注
    notes = String(metadata={'description': '备注'})

