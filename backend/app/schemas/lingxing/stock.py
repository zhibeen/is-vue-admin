"""领星备货单Schema定义"""
from apiflask import Schema
from apiflask.fields import String, Integer, Float, List, Nested
from apiflask.validators import Length, Range


class StockDetailQuerySchema(Schema):
    """查询备货单详情请求Schema"""
    
    stock_id = String(
        required=True,
        metadata={
            'description': '备货单ID',
            'example': 'BH20251218001'
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


class StockDimensionsSchema(Schema):
    """商品尺寸Schema"""
    
    length = Float(
        metadata={
            'description': '长度',
            'example': 20.0
        }
    )
    
    width = Float(
        metadata={
            'description': '宽度',
            'example': 15.0
        }
    )
    
    height = Float(
        metadata={
            'description': '高度',
            'example': 10.0
        }
    )
    
    unit = String(
        metadata={
            'description': '单位',
            'example': 'cm'
        }
    )


class StockItemSchema(Schema):
    """备货单商品明细Schema"""
    
    sku = String(
        required=True,
        metadata={
            'description': '商品SKU',
            'example': 'TEST-SKU-001'
        }
    )
    
    product_name = String(
        metadata={
            'description': '商品名称',
            'example': '测试商品A'
        }
    )
    
    quantity = Integer(
        metadata={
            'description': '备货数量',
            'example': 200
        }
    )
    
    available_quantity = Integer(
        metadata={
            'description': '可用库存',
            'example': 150
        }
    )
    
    weight = Float(
        metadata={
            'description': '单件重量(kg)',
            'example': 0.25
        }
    )
    
    dimensions = Nested(
        StockDimensionsSchema,
        metadata={
            'description': '尺寸信息'
        }
    )


class StockDetailSchema(Schema):
    """备货单详情响应Schema"""
    
    stock_id = String(
        required=True,
        metadata={
            'description': '备货单ID',
            'example': 'BH20251218001'
        }
    )
    
    stock_name = String(
        metadata={
            'description': '备货单名称',
            'example': '美西仓12月补货计划'
        }
    )
    
    warehouse_code = String(
        metadata={
            'description': '仓库代码',
            'example': 'US-WEST-01'
        }
    )
    
    warehouse_name = String(
        metadata={
            'description': '仓库名称',
            'example': '美西仓库1号'
        }
    )
    
    status = String(
        metadata={
            'description': '备货状态',
            'example': 'CONFIRMED'
        }
    )
    
    total_quantity = Integer(
        metadata={
            'description': '总数量',
            'example': 500
        }
    )
    
    total_weight = Float(
        metadata={
            'description': '总重量(kg)',
            'example': 125.5
        }
    )
    
    total_volume = Float(
        metadata={
            'description': '总体积(m³)',
            'example': 2.35
        }
    )
    
    items = List(
        Nested(StockItemSchema),
        metadata={
            'description': '商品明细列表'
        }
    )
    
    created_at = String(
        metadata={
            'description': '创建时间',
            'example': '2025-12-18T09:00:00Z'
        }
    )
    
    updated_at = String(
        metadata={
            'description': '更新时间',
            'example': '2025-12-18T10:30:00Z'
        }
    )

