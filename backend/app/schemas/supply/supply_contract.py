"""开票合同相关Schemas"""
from apiflask import Schema
from apiflask.fields import String, Integer, Float, Date, DateTime, Nested, List as ListField
from marshmallow import validates, ValidationError


class SupplyContractItemSchema(Schema):
    """开票合同明细Schema"""
    id = Integer(dump_only=True)
    contract_id = Integer(dump_only=True)
    
    # 开票商品信息（可能与实际商品不同）
    product_name = String(required=True, metadata={'description': '开票商品名称'})
    specification = String(metadata={'description': '规格型号'})
    
    # 数量信息
    quantity = Float(required=True, metadata={'description': '数量'})
    unit = String(required=True, metadata={'description': '开票单位', 'example': '台'})
    
    # 价格信息
    unit_price = Float(required=True, metadata={'description': '单价（不含税）'})
    total_price = Float(required=True, metadata={'description': '小计（不含税）'})
    
    # 税额
    tax_amount = Float(metadata={'description': '税额'})
    
    # 溯源信息
    source_delivery_item_ids = ListField(
        Integer(),
        metadata={'description': '源交付合同明细ID列表（用于溯源）'}
    )


class SupplyContractSchema(Schema):
    """开票合同Schema（输出）"""
    id = Integer(dump_only=True)
    contract_no = String(dump_only=True, metadata={'description': '开票合同号'})
    
    # 关联信息
    delivery_contract_id = Integer(
        required=True,
        metadata={'description': '主交付合同ID（1对1唯一）'}
    )
    supplier_id = Integer(required=True, metadata={'description': '供应商ID'})
    
    # 金额信息
    total_amount = Float(required=True, metadata={'description': '总金额（不含税）'})
    currency = String(metadata={'description': '币种', 'example': 'CNY'})
    
    # 税务信息
    tax_rate = Float(metadata={'description': '税率', 'example': 0.13})
    total_amount_with_tax = Float(metadata={'description': '含税总额'})
    
    # 状态信息
    status = String(metadata={'description': '合同状态'})
    invoice_status = String(metadata={'description': '开票状态: uninvoiced/partial/invoiced'})
    
    # 开票金额追踪
    invoiced_amount = Float(dump_only=True, metadata={'description': '已开票金额'})
    
    # 开票说明
    notes = String(metadata={'description': '开票说明（如果调整了品名/数量，必填）'})
    
    # 合同日期
    contract_date = Date(metadata={'description': '合同日期'})
    
    # 审计字段
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)
    created_by = Integer(dump_only=True)
    
    # 明细
    items = ListField(Nested(SupplyContractItemSchema), metadata={'description': '开票合同明细'})


class SupplyContractCreateSchema(Schema):
    """开票合同创建Schema"""
    delivery_contract_id = Integer(
        required=True,
        metadata={'description': '主交付合同ID'}
    )
    
    # 模式选择：auto（自动复制）或 manual（手工调整）
    mode = String(
        metadata={
            'description': '生成模式: auto(自动复制)/manual(手工调整)',
            'example': 'auto'
        }
    )
    
    # 税务信息
    tax_rate = Float(metadata={'description': '税率', 'example': 0.13})
    
    # 开票说明（手工调整时必填）
    notes = String(metadata={'description': '开票说明'})
    
    # 合同日期
    contract_date = Date(required=True, metadata={'description': '合同日期'})
    
    # 明细（仅manual模式需要）
    items = ListField(
        Nested(SupplyContractItemSchema),
        metadata={'description': '开票合同明细（manual模式必填）'}
    )
    
    @validates('items')
    def validate_items_with_mode(self, value):
        """根据模式验证明细"""
        # 注意：这里无法直接访问mode字段，需要在service层进行验证
        pass

