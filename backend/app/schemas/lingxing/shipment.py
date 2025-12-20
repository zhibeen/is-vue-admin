"""领星发货单Schema定义"""
from apiflask import Schema
from apiflask.fields import String, Integer, List, Nested
from apiflask.validators import Length, Range


class ShipmentDetailQuerySchema(Schema):
    """查询发货单详情请求Schema"""
    
    shipment_id = String(
        required=True,
        metadata={
            'description': '发货单ID（亚马逊ShipmentId）',
            'example': 'FBA12345678'
        },
        validate=Length(min=1, max=50)
    )
    
    page = Integer(
        load_default=1,
        metadata={
            'description': '页码',
            'example': 1
        },
        validate=Range(min=1)
    )
    
    page_size = Integer(
        load_default=20,
        metadata={
            'description': '每页记录数',
            'example': 20
        },
        validate=Range(min=1, max=100)
    )


class ShipmentAddressSchema(Schema):
    """发货地址Schema"""
    
    name = String(
        metadata={
            'description': '地址名称',
            'example': '深圳仓库'
        }
    )
    
    address_line1 = String(
        metadata={
            'description': '地址第一行',
            'example': '某某区某某路123号'
        }
    )
    
    city = String(
        metadata={
            'description': '城市',
            'example': '深圳'
        }
    )
    
    state_or_province = String(
        metadata={
            'description': '省份/州',
            'example': '广东省'
        }
    )
    
    country_code = String(
        metadata={
            'description': '国家代码',
            'example': 'CN'
        }
    )
    
    postal_code = String(
        metadata={
            'description': '邮政编码',
            'example': '518000'
        }
    )


class ShipmentItemSchema(Schema):
    """发货单商品明细Schema"""
    
    sku = String(
        required=True,
        metadata={
            'description': '商品SKU',
            'example': 'TEST-SKU-001'
        }
    )
    
    fnsku = String(
        metadata={
            'description': '亚马逊仓库SKU',
            'example': 'X001234567'
        }
    )
    
    quantity_shipped = Integer(
        metadata={
            'description': '已发货数量',
            'example': 100
        }
    )
    
    quantity_received = Integer(
        metadata={
            'description': '已入库数量',
            'example': 95
        }
    )
    
    quantity_in_case = Integer(
        metadata={
            'description': '每箱数量',
            'example': 10
        }
    )


class ShipmentDetailSchema(Schema):
    """发货单详情响应Schema"""
    
    shipment_id = String(
        required=True,
        metadata={
            'description': '发货单ID',
            'example': 'FBA12345678'
        }
    )
    
    shipment_name = String(
        metadata={
            'description': '发货单名称',
            'example': '测试发货计划-202512'
        }
    )
    
    destination_fulfillment_center_id = String(
        metadata={
            'description': '目标仓库代码',
            'example': 'PHX3'
        }
    )
    
    label_prep_type = String(
        metadata={
            'description': '标签准备类型',
            'example': 'SELLER_LABEL'
        }
    )
    
    shipment_status = String(
        metadata={
            'description': '发货状态',
            'example': 'SHIPPED'
        }
    )
    
    ship_from_address = Nested(
        ShipmentAddressSchema,
        metadata={
            'description': '发货地址'
        }
    )
    
    items = List(
        Nested(ShipmentItemSchema),
        metadata={
            'description': '商品明细列表'
        }
    )
    
    total_units = Integer(
        metadata={
            'description': '总件数',
            'example': 100
        }
    )
    
    created_date = String(
        metadata={
            'description': '创建时间 (ISO 8601格式)',
            'example': '2025-12-01T10:00:00Z'
        }
    )
    
    updated_date = String(
        metadata={
            'description': '更新时间',
            'example': '2025-12-15T14:30:00Z'
        }
    )

