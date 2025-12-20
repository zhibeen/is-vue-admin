"""发货单物流服务明细Schema"""
from apiflask import Schema
from apiflask.fields import String, Integer, Float, DateTime
from marshmallow import validates, ValidationError


class ShipmentLogisticsServiceSchema(Schema):
    """物流服务明细输出Schema"""
    id = Integer(dump_only=True)
    shipment_id = Integer(
        required=True,
        metadata={
            'description': '发货单ID',
            'example': 1001
        }
    )
    logistics_provider_id = Integer(
        required=True,
        metadata={
            'description': '物流服务商ID',
            'example': 1
        }
    )
    logistics_provider_name = String(
        dump_only=True,
        metadata={
            'description': '物流服务商名称',
            'example': '顺丰速运'
        }
    )
    service_type = String(
        required=True,
        metadata={
            'description': '服务类型',
            'example': 'domestic_trucking'
        }
    )
    service_description = String(
        metadata={
            'description': '服务描述',
            'example': '深圳至上海陆运'
        }
    )
    estimated_amount = Float(
        metadata={
            'description': '预估费用',
            'example': 5000.00
        }
    )
    actual_amount = Float(
        metadata={
            'description': '实际费用',
            'example': 4800.00
        }
    )
    currency = String(
        metadata={
            'description': '币种',
            'example': 'CNY'
        }
    )
    payment_method = String(
        metadata={
            'description': '付款方式',
            'example': 'postpaid'
        }
    )
    service_voucher_id = Integer(
        dump_only=True,
        metadata={
            'description': '服务凭证ID'
        }
    )
    payment_voucher_id = Integer(
        dump_only=True,
        metadata={
            'description': '付款凭证ID'
        }
    )
    status = String(
        dump_only=True,
        metadata={
            'description': '状态: pending/confirmed/reconciled/paid',
            'example': 'pending'
        }
    )
    confirmed_at = DateTime(
        dump_only=True,
        metadata={'description': '确认时间'}
    )
    reconciled_at = DateTime(
        dump_only=True,
        metadata={'description': '对账时间'}
    )
    paid_at = DateTime(
        dump_only=True,
        metadata={'description': '付款时间'}
    )
    notes = String(
        metadata={
            'description': '备注'
        }
    )
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)


class ShipmentLogisticsServiceCreateSchema(Schema):
    """物流服务明细创建Schema"""
    logistics_provider_id = Integer(
        required=True,
        metadata={
            'description': '物流服务商ID',
            'example': 1
        }
    )
    service_type = String(
        required=True,
        metadata={
            'description': '服务类型',
            'example': 'domestic_trucking'
        }
    )
    service_description = String(
        metadata={
            'description': '服务描述',
            'example': '深圳至上海陆运'
        }
    )
    estimated_amount = Float(
        metadata={
            'description': '预估费用',
            'example': 5000.00
        }
    )
    actual_amount = Float(
        metadata={
            'description': '实际费用',
            'example': 4800.00
        }
    )
    currency = String(
        metadata={
            'description': '币种',
            'example': 'CNY'
        }
    )
    payment_method = String(
        metadata={
            'description': '付款方式',
            'example': 'postpaid'
        }
    )
    notes = String(
        metadata={
            'description': '备注'
        }
    )
    
    @validates('estimated_amount')
    def validate_estimated_amount(self, value):
        """验证预估费用"""
        if value is not None and value < 0:
            raise ValidationError('预估费用不能为负数')
        return value
    
    @validates('actual_amount')
    def validate_actual_amount(self, value):
        """验证实际费用"""
        if value is not None and value < 0:
            raise ValidationError('实际费用不能为负数')
        return value


class ShipmentLogisticsServiceUpdateSchema(Schema):
    """物流服务明细更新Schema"""
    logistics_provider_id = Integer(
        metadata={'description': '物流服务商ID'}
    )
    service_type = String(
        metadata={'description': '服务类型'}
    )
    service_description = String(
        metadata={'description': '服务描述'}
    )
    estimated_amount = Float(
        metadata={'description': '预估费用'}
    )
    actual_amount = Float(
        metadata={'description': '实际费用'}
    )
    currency = String(
        metadata={'description': '币种'}
    )
    payment_method = String(
        metadata={'description': '付款方式'}
    )
    notes = String(
        metadata={'description': '备注'}
    )
    
    @validates('estimated_amount')
    def validate_estimated_amount(self, value):
        """验证预估费用"""
        if value is not None and value < 0:
            raise ValidationError('预估费用不能为负数')
        return value
    
    @validates('actual_amount')
    def validate_actual_amount(self, value):
        """验证实际费用"""
        if value is not None and value < 0:
            raise ValidationError('实际费用不能为负数')
        return value

