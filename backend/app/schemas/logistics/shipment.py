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
    hs_code = String(metadata={'description': 'HS编码', 'example': '8708.29.10'})
    export_name = String(metadata={'description': '出口申报名称', 'example': '汽车零部件'})
    customs_product_id = Integer(metadata={'description': '归类商品ID'})
    
    # 数量信息
    quantity = Float(required=True, metadata={'description': '数量'})
    unit = String(metadata={'description': '单位', 'example': 'PCS'})
    customs_unit = String(metadata={'description': '海关申报单位', 'example': '千克'})
    
    # 价格信息（不含税）
    unit_price = Float(metadata={'description': '单价（不含税）'})
    total_price = Float(metadata={'description': '总价（不含税）'})
    
    # 税务信息
    tax_rate = Float(metadata={'description': '税率(如0.13表示13%)', 'example': 0.13})
    tax_amount = Float(metadata={'description': '税额'})
    unit_price_with_tax = Float(metadata={'description': '含税单价'})
    total_price_with_tax = Float(metadata={'description': '含税总价'})
    
    # 采购信息
    purchase_order_id = Integer(metadata={'description': '采购单ID'})
    supplier_id = Integer(metadata={'description': '主供应商ID'})
    supplier_name = String(metadata={'description': '主供应商名称'})
    
    # FBA专用字段
    fnsku = String(metadata={'description': '亚马逊FNSKU'})
    msku = String(metadata={'description': '商家SKU(MSKU)'})
    asin = String(metadata={'description': 'ASIN码'})
    marketplace_listing_id = String(metadata={'description': '市场Listing ID'})
    
    # 第三方仓专用字段
    warehouse_matched_qty = Float(metadata={'description': '配对数量'})
    warehouse_received_qty = Float(metadata={'description': '已收数量'})
    warehouse_pending_qty = Float(metadata={'description': '待收数量'})
    shelf_location = String(metadata={'description': '货架位置'})
    
    # 包装信息
    package_no = String(metadata={'description': '箱号'})
    barcode = String(metadata={'description': '箱码/条码'})
    
    # 重量体积
    unit_weight = Float(metadata={'description': '单件重量(kg)'})
    unit_volume = Float(metadata={'description': '单件体积(m³)'})
    total_weight = Float(metadata={'description': '总重量(kg)'})
    
    # 原产地
    origin_country = String(metadata={'description': '原产国'})
    
    # 外部系统信息
    external_item_id = String(metadata={'description': '外部商品ID'})


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
    shipper_company_name = String(dump_only=True, metadata={'description': '发货公司名称'})
    consignee_id = Integer(metadata={'description': '境外收货人ID'})
    consignee_name = String(metadata={'description': '收货人名称'})
    consignee_address = String(metadata={'description': '收货地址'})
    consignee_country = String(metadata={'description': '收货国家'})
    
    # 仓库信息
    origin_warehouse_id = Integer(metadata={'description': '发货仓库ID'})
    origin_warehouse_name = String(metadata={'description': '发货仓库名称'})
    origin_warehouse_type = String(metadata={'description': '发货仓库类型', 'example': 'self/factory/supplier'})
    origin_warehouse_address = String(metadata={'description': '发货仓库地址'})
    is_factory_direct = Integer(metadata={'description': '是否工厂直发', 'example': 0})
    
    destination_warehouse_id = Integer(metadata={'description': '收货仓库ID'})
    destination_warehouse_name = String(metadata={'description': '收货仓库名称'})
    destination_warehouse_code = String(metadata={'description': '收货仓库编码', 'example': 'WPLA16'})
    destination_warehouse_type = String(metadata={'description': '仓库类型', 'example': 'fba/third_party/self'})
    destination_warehouse_address = String(metadata={'description': '收货仓库地址'})
    
    # FBA专用字段
    fba_shipment_id = String(metadata={'description': 'FBA发货计划ID'})
    fba_center_codes = ListField(String, metadata={'description': 'FBA中心编码数组', 'example': ['PDX7', 'LGB6']})
    marketplace = String(metadata={'description': '市场站点', 'example': 'US/UK/DE/JP'})
    
    # 第三方仓专用字段
    warehouse_service_provider = String(metadata={'description': '仓储服务商'})
    warehouse_contact = String(metadata={'description': '仓库联系人'})
    warehouse_contact_phone = String(metadata={'description': '仓库联系电话'})
    
    # 物流信息
    logistics_provider = String(metadata={'description': '物流商'})
    logistics_service_type = String(metadata={'description': '物流服务类型'})
    tracking_no = String(metadata={'description': '物流跟踪号'})
    shipping_method = String(metadata={'description': '运输方式', 'example': 'air/sea/express/land/sea_air'})
    freight_term = String(metadata={'description': '运费支付方式', 'example': 'prepaid/collect/third_party'})
    
    # 时间节点
    estimated_ship_date = Date(metadata={'description': '预计发货日期'})
    actual_ship_date = Date(metadata={'description': '实际发货日期'})
    estimated_arrival_date = Date(metadata={'description': '预计到货日期'})
    actual_arrival_date = Date(metadata={'description': '实际到货日期'})
    warehouse_received_date = DateTime(metadata={'description': '仓库签收时间'})
    completed_date = DateTime(metadata={'description': '完成时间'})
    
    # 包装信息
    total_packages = Integer(metadata={'description': '总件数'})
    packing_method = String(metadata={'description': '包装方式', 'example': '纸箱/托盘/散装'})
    total_gross_weight = Float(metadata={'description': '总毛重(kg)'})
    total_net_weight = Float(metadata={'description': '总净重(kg)'})
    total_volume = Float(metadata={'description': '总体积(m³)'})
    volumetric_weight = Float(metadata={'description': '体积重(kg)'})
    chargeable_weight = Float(metadata={'description': '计费重量(kg)'})
    
    # 金额与财务信息
    currency = String(metadata={'description': '币种', 'example': 'USD'})
    
    # ===== 物流成本（核心字段） ===== #
    freight_cost = Float(metadata={'description': '运费'})
    insurance_cost = Float(metadata={'description': '保险费'})
    handling_fee = Float(metadata={'description': '操作费'})
    other_costs = Float(metadata={'description': '其他费用'})
    total_logistics_cost = Float(metadata={'description': '物流总成本'})
    
    # ===== 以下字段已废弃，将在v2.0移除 ===== #
    total_goods_value = Float(metadata={'description': '[DEPRECATED] 货物总价值 - 请从商品明细计算'})
    declared_value = Float(metadata={'description': '[DEPRECATED] 申报价值 - 请从报关单获取'})
    
    vat_number = String(metadata={'description': '[DEPRECATED] VAT税号 - 请从公司/收货人主表获取'})
    tax_rate = Float(metadata={'description': '[DEPRECATED] 税率 - 请从税务配置获取'})
    estimated_tax = Float(metadata={'description': '[DEPRECATED] 预估税费 - 请从税务系统获取'})
    actual_tax = Float(metadata={'description': '[DEPRECATED] 实际税费 - 请从税务系统获取'})
    
    total_purchase_cost = Float(metadata={'description': '[DEPRECATED] 采购总成本 - 请从采购明细汇总'})
    profit_margin = Float(metadata={'description': '[DEPRECATED] 利润率 - 请从财务系统计算'})
    cost_allocation_method = String(metadata={'description': '[DEPRECATED] 成本分摊方式 - 请从财务配置获取'})
    
    total_amount = Float(metadata={'description': '[DEPRECATED] 总金额（不含税）- 仅供参考'})
    total_tax_amount = Float(metadata={'description': '[DEPRECATED] 总税额 - 仅供参考'})
    total_amount_with_tax = Float(metadata={'description': '[DEPRECATED] 含税总金额 - 仅供参考'})
    
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
    
    # 仓库信息
    origin_warehouse_id = Integer(metadata={'description': '发货仓库ID'})
    origin_warehouse_name = String(metadata={'description': '发货仓库名称'})
    origin_warehouse_type = String(metadata={'description': '发货仓库类型'})
    origin_warehouse_address = String(metadata={'description': '发货仓库地址'})
    is_factory_direct = Integer(metadata={'description': '是否工厂直发'})
    
    destination_warehouse_id = Integer(metadata={'description': '收货仓库ID'})
    destination_warehouse_name = String(metadata={'description': '收货仓库名称'})
    destination_warehouse_code = String(metadata={'description': '收货仓库编码'})
    destination_warehouse_type = String(metadata={'description': '仓库类型'})
    destination_warehouse_address = String(metadata={'description': '收货仓库地址'})
    
    fba_shipment_id = String(metadata={'description': 'FBA发货计划ID'})
    fba_center_codes = ListField(String, metadata={'description': 'FBA中心编码数组'})
    marketplace = String(metadata={'description': '市场站点'})
    
    warehouse_service_provider = String(metadata={'description': '仓储服务商'})
    warehouse_contact = String(metadata={'description': '仓库联系人'})
    warehouse_contact_phone = String(metadata={'description': '仓库联系电话'})
    
    # 物流信息
    logistics_provider = String(metadata={'description': '物流商'})
    logistics_service_type = String(metadata={'description': '物流服务类型'})
    tracking_no = String(metadata={'description': '物流跟踪号'})
    shipping_method = String(metadata={'description': '运输方式'})
    freight_term = String(metadata={'description': '运费支付方式'})
    estimated_ship_date = Date(metadata={'description': '预计发货日期'})
    estimated_arrival_date = Date(metadata={'description': '预计到货日期'})
    
    # 包装信息
    total_packages = Integer(metadata={'description': '总件数'})
    packing_method = String(metadata={'description': '包装方式'})
    total_gross_weight = Float(metadata={'description': '总毛重(kg)'})
    total_net_weight = Float(metadata={'description': '总净重(kg)'})
    total_volume = Float(metadata={'description': '总体积(m³)'})
    volumetric_weight = Float(metadata={'description': '体积重(kg)'})
    chargeable_weight = Float(metadata={'description': '计费重量(kg)'})
    
    # 金额与财务信息
    currency = String(metadata={'description': '币种', 'example': 'USD'})
    
    # 物流成本（核心字段）
    freight_cost = Float(metadata={'description': '运费'})
    insurance_cost = Float(metadata={'description': '保险费'})
    handling_fee = Float(metadata={'description': '操作费'})
    other_costs = Float(metadata={'description': '其他费用'})
    
    # 以下字段已废弃（可选填写，仅供参考）
    total_goods_value = Float(metadata={'description': '[DEPRECATED] 货物总价值'})
    declared_value = Float(metadata={'description': '[DEPRECATED] 申报价值'})
    vat_number = String(metadata={'description': '[DEPRECATED] VAT税号'})
    tax_rate = Float(metadata={'description': '[DEPRECATED] 税率'})
    estimated_tax = Float(metadata={'description': '预估税费'})
    
    cost_allocation_method = String(metadata={'description': '成本分摊方式'})
    
    # 原有金额字段（保留向后兼容）
    total_amount = Float(metadata={'description': '总金额（不含税）'})
    total_tax_amount = Float(metadata={'description': '总税额'})
    total_amount_with_tax = Float(metadata={'description': '含税总金额'})
    
    # 备注
    notes = String(metadata={'description': '备注'})
    
    # 明细（必填）
    items = ListField(
        Nested(ShipmentOrderItemSchema),
        required=True,
        metadata={'description': '发货明细列表'}
    )
    
    @validates('items')
    def validate_items(self, value, **kwargs):
        if not value or len(value) == 0:
            raise ValidationError('发货明细不能为空')


class ShipmentOrderUpdateSchema(Schema):
    """发货单更新Schema"""
    status = String(metadata={'description': '状态'})
    
    # 基本信息
    consignee_id = Integer(metadata={'description': '境外收货人ID'})
    consignee_name = String(metadata={'description': '收货人名称'})
    consignee_address = String(metadata={'description': '收货地址'})
    consignee_country = String(metadata={'description': '收货国家'})
    
    # 仓库信息
    origin_warehouse_id = Integer(metadata={'description': '发货仓库ID'})
    origin_warehouse_name = String(metadata={'description': '发货仓库名称'})
    origin_warehouse_type = String(metadata={'description': '发货仓库类型'})
    origin_warehouse_address = String(metadata={'description': '发货仓库地址'})
    is_factory_direct = Integer(metadata={'description': '是否工厂直发'})
    
    destination_warehouse_id = Integer(metadata={'description': '收货仓库ID'})
    destination_warehouse_name = String(metadata={'description': '收货仓库名称'})
    destination_warehouse_code = String(metadata={'description': '收货仓库编码'})
    destination_warehouse_type = String(metadata={'description': '仓库类型'})
    destination_warehouse_address = String(metadata={'description': '收货仓库地址'})
    
    fba_shipment_id = String(metadata={'description': 'FBA发货计划ID'})
    fba_center_codes = ListField(String, metadata={'description': 'FBA中心编码数组'})
    marketplace = String(metadata={'description': '市场站点'})
    
    warehouse_service_provider = String(metadata={'description': '仓储服务商'})
    warehouse_contact = String(metadata={'description': '仓库联系人'})
    warehouse_contact_phone = String(metadata={'description': '仓库联系电话'})
    
    # 物流信息
    logistics_provider = String(metadata={'description': '物流商'})
    logistics_service_type = String(metadata={'description': '物流服务类型'})
    tracking_no = String(metadata={'description': '物流跟踪号'})
    shipping_method = String(metadata={'description': '运输方式'})
    freight_term = String(metadata={'description': '运费支付方式'})
    estimated_ship_date = Date(metadata={'description': '预计发货日期'})
    actual_ship_date = Date(metadata={'description': '实际发货日期'})
    estimated_arrival_date = Date(metadata={'description': '预计到货日期'})
    actual_arrival_date = Date(metadata={'description': '实际到货日期'})
    warehouse_received_date = DateTime(metadata={'description': '仓库签收时间'})
    
    # 包装信息
    total_packages = Integer(metadata={'description': '总件数'})
    packing_method = String(metadata={'description': '包装方式'})
    total_gross_weight = Float(metadata={'description': '总毛重(kg)'})
    total_net_weight = Float(metadata={'description': '总净重(kg)'})
    total_volume = Float(metadata={'description': '总体积(m³)'})
    volumetric_weight = Float(metadata={'description': '体积重(kg)'})
    chargeable_weight = Float(metadata={'description': '计费重量(kg)'})
    
    # 金额与财务信息
    currency = String(metadata={'description': '币种'})
    total_goods_value = Float(metadata={'description': '货物总价值'})
    declared_value = Float(metadata={'description': '申报价值'})
    
    freight_cost = Float(metadata={'description': '运费'})
    insurance_cost = Float(metadata={'description': '保险费'})
    handling_fee = Float(metadata={'description': '操作费'})
    other_costs = Float(metadata={'description': '其他费用'})
    
    vat_number = String(metadata={'description': 'VAT税号'})
    tax_rate = Float(metadata={'description': '税率'})
    estimated_tax = Float(metadata={'description': '预估税费'})
    actual_tax = Float(metadata={'description': '实际税费'})
    
    cost_allocation_method = String(metadata={'description': '成本分摊方式'})
    
    # 备注
    notes = String(metadata={'description': '备注'})

