"""物流服务商序列化Schema"""
from apiflask import Schema
from apiflask.fields import String, Boolean, List as ListField, Integer, DateTime
from marshmallow import validates, ValidationError


class LogisticsProviderSchema(Schema):
    """物流服务商输出Schema"""
    id = Integer(dump_only=True)
    provider_name = String(
        required=True, 
        metadata={
            'description': '服务商名称', 
            'example': '顺丰速运'
        }
    )
    provider_code = String(
        required=True, 
        metadata={
            'description': '服务商编码', 
            'example': 'SF001'
        }
    )
    service_type = String(
        metadata={
            'description': '服务类型: domestic_trucking/international_sea/international_air/customs_clearance/destination_delivery',
            'example': 'domestic_trucking'
        }
    )
    payment_method = String(
        metadata={
            'description': '付款方式: prepaid/immediate/postpaid',
            'example': 'postpaid'
        }
    )
    settlement_cycle = String(
        metadata={
            'description': '结算周期: immediate/weekly/monthly',
            'example': 'monthly'
        }
    )
    contact_name = String(
        metadata={
            'description': '联系人',
            'example': '张三'
        }
    )
    contact_phone = String(
        metadata={
            'description': '联系电话',
            'example': '13800138000'
        }
    )
    contact_email = String(
        metadata={
            'description': '邮箱',
            'example': 'contact@sf.com'
        }
    )
    bank_name = String(
        metadata={
            'description': '开户银行',
            'example': '中国工商银行深圳分行'
        }
    )
    bank_account = String(
        metadata={
            'description': '银行账号',
            'example': '6222024000012345678'
        }
    )
    bank_account_name = String(
        metadata={
            'description': '账户名称',
            'example': '深圳顺丰速运有限公司'
        }
    )
    service_areas = ListField(
        String(),
        metadata={
            'description': '服务区域',
            'example': ['广东省', '上海市']
        }
    )
    is_active = Boolean(
        metadata={
            'description': '启用状态',
            'example': True
        }
    )
    notes = String(
        metadata={
            'description': '备注'
        }
    )
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)


class LogisticsProviderCreateSchema(Schema):
    """物流服务商创建Schema"""
    provider_name = String(
        required=True,
        metadata={
            'description': '服务商名称',
            'example': '顺丰速运'
        }
    )
    provider_code = String(
        required=True,
        metadata={
            'description': '服务商编码',
            'example': 'SF001'
        }
    )
    service_type = String(
        metadata={
            'description': '服务类型',
            'example': 'domestic_trucking'
        }
    )
    payment_method = String(
        metadata={
            'description': '付款方式',
            'example': 'postpaid'
        }
    )
    settlement_cycle = String(
        metadata={
            'description': '结算周期',
            'example': 'monthly'
        }
    )
    contact_name = String(
        metadata={'description': '联系人'}
    )
    contact_phone = String(
        metadata={'description': '联系电话'}
    )
    contact_email = String(
        metadata={'description': '邮箱'}
    )
    bank_name = String(
        metadata={'description': '开户银行'}
    )
    bank_account = String(
        metadata={'description': '银行账号'}
    )
    bank_account_name = String(
        metadata={'description': '账户名称'}
    )
    service_areas = ListField(
        String(),
        metadata={'description': '服务区域'}
    )
    is_active = Boolean(
        metadata={'description': '启用状态'}
    )
    notes = String(
        metadata={'description': '备注'}
    )
    
    @validates('provider_code')
    def validate_provider_code(self, value):
        """验证服务商编码格式"""
        if not value or len(value) < 2:
            raise ValidationError('服务商编码至少需要2个字符')
        return value


class LogisticsProviderUpdateSchema(Schema):
    """物流服务商更新Schema"""
    provider_name = String(
        metadata={'description': '服务商名称'}
    )
    service_type = String(
        metadata={'description': '服务类型'}
    )
    payment_method = String(
        metadata={'description': '付款方式'}
    )
    settlement_cycle = String(
        metadata={'description': '结算周期'}
    )
    contact_name = String(
        metadata={'description': '联系人'}
    )
    contact_phone = String(
        metadata={'description': '联系电话'}
    )
    contact_email = String(
        metadata={'description': '邮箱'}
    )
    bank_name = String(
        metadata={'description': '开户银行'}
    )
    bank_account = String(
        metadata={'description': '银行账号'}
    )
    bank_account_name = String(
        metadata={'description': '账户名称'}
    )
    service_areas = ListField(
        String(),
        metadata={'description': '服务区域'}
    )
    is_active = Boolean(
        metadata={'description': '启用状态'}
    )
    notes = String(
        metadata={'description': '备注'}
    )
