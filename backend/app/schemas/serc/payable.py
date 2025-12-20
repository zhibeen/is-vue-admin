"""
财务应付单相关 Schema
"""
from marshmallow import Schema, fields, validates, ValidationError
from datetime import date
from app.schemas.system import UserSimpleSchema


class FinPayableSchema(Schema):
    """财务应付单基础 Schema"""
    id = fields.Integer(dump_only=True)
    payable_no = fields.String(dump_only=True)
    
    # 来源信息
    source_type = fields.String(
        required=True,
        metadata={'description': '来源类型', 'example': 'logistics'}
    )
    source_id = fields.Integer(required=True, metadata={'description': '来源单据ID', 'example': 123})
    source_no = fields.String(metadata={'description': '来源单号', 'example': 'LS20250120001'})
    
    # 收款方信息
    payee_type = fields.String(
        required=True,
        metadata={'description': '收款方类型', 'example': 'logistics_provider'}
    )
    payee_id = fields.Integer(required=True, metadata={'description': '收款方ID', 'example': 5})
    payee_name = fields.String(required=True, metadata={'description': '收款方名称', 'example': 'DHL快递'})
    bank_name = fields.String(metadata={'description': '开户银行'})
    bank_account = fields.String(metadata={'description': '银行账号'})
    bank_account_name = fields.String(metadata={'description': '账户名称'})
    
    # 金额信息
    payable_amount = fields.Decimal(
        as_string=True,
        required=True,
        metadata={'description': '应付金额', 'example': '15000.00'}
    )
    paid_amount = fields.Decimal(as_string=True, dump_only=True)
    remaining_amount = fields.Method('get_remaining_amount', dump_only=True)
    currency = fields.String(metadata={'description': '币种', 'example': 'CNY'})
    
    # 付款计划
    due_date = fields.Date(metadata={'description': '应付日期', 'example': '2025-02-20'})
    priority = fields.Integer(metadata={'description': '优先级(1-5)', 'example': 3})
    
    # 状态信息
    status = fields.String(dump_only=True)
    approved_by_id = fields.Integer(dump_only=True)
    approved_at = fields.DateTime(dump_only=True)
    rejection_reason = fields.String(dump_only=True)
    
    # 付款执行
    payment_pool_id = fields.Integer(dump_only=True)
    paid_at = fields.DateTime(dump_only=True)
    payment_voucher_id = fields.Integer(dump_only=True)
    
    # 备注
    notes = fields.String(metadata={'description': '备注'})
    
    # 审计字段
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by_id = fields.Integer(dump_only=True)
    
    def get_remaining_amount(self, obj):
        """计算剩余金额"""
        return str(obj.payable_amount - obj.paid_amount)


class CreatePayableSchema(Schema):
    """创建应付单 Schema"""
    source_type = fields.String(required=True)
    source_id = fields.Integer(required=True)
    source_no = fields.String()
    payee_type = fields.String(required=True)
    payee_id = fields.Integer(required=True)
    payee_name = fields.String(required=True)
    bank_name = fields.String()
    bank_account = fields.String()
    bank_account_name = fields.String()
    payable_amount = fields.Decimal(as_string=True, required=True)
    currency = fields.String(load_default='CNY')
    due_date = fields.Date()
    priority = fields.Integer(load_default=3)
    notes = fields.String()


class ApprovalSchema(Schema):
    """审批应付单 Schema"""
    action = fields.String(
        required=True,
        metadata={'description': '审批操作', 'example': 'approve'}
    )
    rejection_reason = fields.String(metadata={'description': '驳回原因（驳回时必填）'})
    add_to_pool = fields.Boolean(
        load_default=False,
        metadata={'description': '批准后是否立即加入付款池', 'example': True}
    )
    pool_id = fields.Integer(metadata={'description': '付款池ID（可选）'})


class AddToPoolSchema(Schema):
    """加入付款池 Schema"""
    pool_id = fields.Integer(required=True, metadata={'description': '付款池ID', 'example': 1})


class MarkPaidSchema(Schema):
    """标记已付款 Schema"""
    paid_amount = fields.Decimal(
        as_string=True,
        required=True,
        metadata={'description': '付款金额', 'example': '15000.00'}
    )
    paid_at = fields.DateTime(metadata={'description': '付款时间（可选，默认当前时间）'})
    payment_voucher_id = fields.Integer(metadata={'description': '付款凭证ID'})


class FinPaymentPoolSchema(Schema):
    """付款池 Schema"""
    id = fields.Integer(dump_only=True)
    pool_no = fields.String(dump_only=True)
    pool_name = fields.String(required=True, metadata={'description': '付款池名称', 'example': '2025年1月付款池'})
    scheduled_date = fields.Date(
        required=True,
        metadata={'description': '计划付款日期', 'example': '2025-01-31'}
    )
    total_amount = fields.Decimal(as_string=True, dump_only=True)
    total_count = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)
    approved_by_id = fields.Integer(dump_only=True)
    approved_at = fields.DateTime(dump_only=True)
    executed_by_id = fields.Integer(dump_only=True)
    executed_at = fields.DateTime(dump_only=True)
    notes = fields.String()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CreatePaymentPoolSchema(Schema):
    """创建付款池 Schema"""
    pool_name = fields.String(required=True)
    scheduled_date = fields.Date(required=True)
    notes = fields.String()


class FinPayableDetailSchema(FinPayableSchema):
    """应付单详情 Schema（包含关联数据）"""
    approved_by = fields.Nested(UserSimpleSchema, dump_only=True)
    payment_pool = fields.Nested(FinPaymentPoolSchema, dump_only=True)


