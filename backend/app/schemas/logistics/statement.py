"""
物流对账单相关 Schema
"""
from marshmallow import Schema, fields, validates, ValidationError
from datetime import date
from app.schemas.system import UserSimpleSchema


class LogisticsStatementSchema(Schema):
    """物流对账单基础 Schema"""
    id = fields.Integer(dump_only=True)
    statement_no = fields.String(dump_only=True)
    logistics_provider_id = fields.Integer(required=True, metadata={'description': '物流服务商ID', 'example': 1})
    
    # 对账周期
    statement_period_start = fields.Date(required=True, metadata={'description': '对账周期开始日期', 'example': '2025-01-01'})
    statement_period_end = fields.Date(required=True, metadata={'description': '对账周期结束日期', 'example': '2025-01-31'})
    
    # 金额信息
    total_amount = fields.Decimal(as_string=True, metadata={'description': '对账总额', 'example': '15000.00'})
    currency = fields.String(metadata={'description': '币种', 'example': 'CNY'})
    
    # 状态信息
    status = fields.String(dump_only=True, metadata={'description': '状态（draft/confirmed/submitted/approved/paid）'})
    confirmed_by_id = fields.Integer(dump_only=True)
    confirmed_at = fields.DateTime(dump_only=True)
    
    # 财务关联
    finance_payable_id = fields.Integer(dump_only=True, metadata={'description': '关联的财务应付单ID'})
    submitted_to_finance_at = fields.DateTime(dump_only=True)
    
    # 附件
    attachment_ids = fields.List(fields.Integer(), metadata={'description': '附件ID列表'})
    
    # 备注
    notes = fields.String(metadata={'description': '备注'})
    
    # 审计字段
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by_id = fields.Integer(dump_only=True)


class CreateStatementSchema(Schema):
    """创建对账单 Schema"""
    logistics_provider_id = fields.Integer(required=True, metadata={'description': '物流服务商ID', 'example': 1})
    statement_period_start = fields.Date(required=True, metadata={'description': '对账周期开始日期', 'example': '2025-01-01'})
    statement_period_end = fields.Date(required=True, metadata={'description': '对账周期结束日期', 'example': '2025-01-31'})
    auto_include_services = fields.Boolean(load_default=False, metadata={'description': '是否自动包含周期内的物流服务', 'example': True})
    notes = fields.String(metadata={'description': '备注'})
    
    @validates('statement_period_start')
    def validate_start_date(self, value):
        if value > date.today():
            raise ValidationError('对账周期开始日期不能晚于今天')


class UpdateStatementSchema(Schema):
    """更新对账单 Schema"""
    statement_period_start = fields.Date(metadata={'description': '对账周期开始日期'})
    statement_period_end = fields.Date(metadata={'description': '对账周期结束日期'})
    attachment_ids = fields.List(fields.Integer(), metadata={'description': '附件ID列表'})
    notes = fields.String(metadata={'description': '备注'})


class AddServiceToStatementSchema(Schema):
    """添加物流服务到对账单 Schema"""
    service_id = fields.Integer(required=True, metadata={'description': '物流服务ID', 'example': 5})
    reconciled_amount = fields.Decimal(as_string=True, metadata={'description': '对账金额（可选，默认使用服务实际费用）', 'example': '500.00'})


class StatementSubmitResponseSchema(Schema):
    """提交对账单响应 Schema"""
    statement_id = fields.Integer()
    finance_payable_id = fields.Integer()
    finance_payable_no = fields.String()
    submitted_at = fields.DateTime()


class LogisticsServiceInStatementSchema(Schema):
    """对账单中的物流服务 Schema"""
    id = fields.Integer()
    shipment_id = fields.Integer()
    shipment_no = fields.String()
    service_type = fields.String()
    service_description = fields.String()
    estimated_amount = fields.Decimal(as_string=True)
    actual_amount = fields.Decimal(as_string=True)
    reconciled_amount = fields.Decimal(as_string=True, metadata={'description': '本次对账金额'})
    currency = fields.String()
    status = fields.String()


class LogisticsStatementDetailSchema(LogisticsStatementSchema):
    """对账单详情 Schema（包含关联的物流服务）"""
    logistics_provider = fields.Nested('LogisticsProviderSimpleSchema', dump_only=True)
    logistics_services = fields.List(fields.Nested(LogisticsServiceInStatementSchema), dump_only=True)
    confirmed_by = fields.Nested(UserSimpleSchema, dump_only=True)


class LogisticsProviderSimpleSchema(Schema):
    """物流服务商简化 Schema"""
    id = fields.Integer()
    provider_name = fields.String()
    provider_code = fields.String()
    service_type = fields.String()
    bank_name = fields.String()
    bank_account = fields.String()
    bank_account_name = fields.String()


