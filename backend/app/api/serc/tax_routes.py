from apiflask import APIBlueprint, Schema
from apiflask.fields import Integer, String, Decimal, List, Boolean, Nested, Date
from apiflask.views import MethodView
from app.services.serc.tax_refund_service import tax_refund_service
from app.services.serc.risk_control_service import risk_control_service

bp = APIBlueprint('serc_tax', __name__, url_prefix='/tax', tag='SERC 税务风控')

# --- Schemas ---
# (Some schemas removed as they are moved to customs module)

class MatchPlanItemSchema(Schema):
    invoice_item_id = Integer()
    invoice_no = String()
    take_qty = Decimal()

class MatchResultItemSchema(Schema):
    item_id = Integer()
    product_name = String()
    status = String() # success/fail
    reason = String()
    plan = List(Nested(MatchPlanItemSchema))

class MatchResponseSchema(Schema):
    success = Boolean()
    results = List(Nested(MatchResultItemSchema))

class ConfirmMatchResponseSchema(Schema):
    success = Boolean()
    message = String()

class CancelMatchResponseSchema(Schema):
    success = Boolean()
    message = String()

class RiskCheckRequestSchema(Schema):
    fob_amount = Decimal(required=True)
    cost_amount = Decimal(required=True)
    currency = String(load_default='USD')

class RiskCheckResponseSchema(Schema):
    is_blocked = Boolean()
    reason = String()
    cost = Decimal()
    safe_range = List(Decimal())

# --- Views ---

@bp.route('/match-declaration/<int:id>')
class TaxMatchAPI(MethodView):
    @bp.doc(summary="执行报关单-发票匹配", description="执行报关单项号级凑数算法，返回匹配计划")
    @bp.output(MatchResponseSchema)
    def post(self, id):
        """为报关单执行发票匹配 (自动凑数)"""
        return tax_refund_service.match_declaration(id)

@bp.route('/match-declaration/<int:id>/confirm')
class TaxMatchConfirmAPI(MethodView):
    @bp.doc(summary="确认匹配结果", description="确认匹配计划并锁定发票状态")
    @bp.output(ConfirmMatchResponseSchema)
    def post(self, id):
        """确认匹配并锁定发票"""
        success = tax_refund_service.confirm_match(id)
        if success:
            return {'success': True, 'message': 'Match confirmed and invoices locked'}
        return {'success': False, 'message': 'Failed to confirm match (plan may have changed)'}, 400

@bp.route('/match-declaration/<int:id>/cancel')
class TaxMatchCancelAPI(MethodView):
    @bp.doc(summary="解除匹配 (释放发票)", description="将报关单回滚至草稿状态，释放已占用的发票额度")
    @bp.output(CancelMatchResponseSchema)
    def post(self, id):
        """解除匹配并释放发票"""
        success = tax_refund_service.cancel_match(id)
        if success:
            return {'success': True, 'message': 'Match cancelled and invoices released'}
        return {'success': False, 'message': 'Failed to cancel match (invalid status)'}, 400

@bp.route('/check-risk')
class RiskCheckAPI(MethodView):
    @bp.doc(summary="换汇成本风控检查", description="计算换汇成本，返回是否阻断及原因")
    @bp.input(RiskCheckRequestSchema, arg_name='data')
    @bp.output(RiskCheckResponseSchema)
    def post(self, data):
        """换汇成本风控检查"""
        return risk_control_service.check_exchange_rate_risk(
            data['fob_amount'],
            data['cost_amount'],
            data['currency']
        )
