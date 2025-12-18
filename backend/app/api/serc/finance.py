from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.schemas.serc.finance import (
    SOAGenerateSchema, SOAItemSchema, SOASearchSchema,
    PaymentPoolItemSchema, PaymentCreateSchema, PaymentRequestSchema
)
from app.schemas.serc.common import PaymentTermSchema
from app.models.serc.finance import FinPurchaseSOA, FinPaymentPool, SysPaymentTerm
from app.models.serc.enums import PaymentPoolStatus
from app.services.serc.finance_service import finance_service
from app.extensions import db
from sqlalchemy import select

serc_finance_bp = APIBlueprint('serc_finance', __name__, url_prefix='/finance', tag='SERC-Finance')

# --- L2: Purchase SOA ---

class SOAListAPI(MethodView):
    @serc_finance_bp.input(SOASearchSchema, location='query')
    @serc_finance_bp.output(SOAItemSchema(many=True))
    def get(self, query_data):
        """获取 L2 结算单列表"""
        query = select(FinPurchaseSOA).order_by(FinPurchaseSOA.id.desc())
        
        if query_data.get('soa_no'):
            query = query.filter(FinPurchaseSOA.soa_no.ilike(f"%{query_data['soa_no']}%"))
        if query_data.get('supplier_id'):
            query = query.filter(FinPurchaseSOA.supplier_id == query_data['supplier_id'])
        if query_data.get('payment_status'):
            query = query.filter(FinPurchaseSOA.payment_status == query_data['payment_status'])
            
        # 简单的分页逻辑 (APIFlask/SQLAlchemy pagination)
        # 这里为了简化返回 list，实际生产建议用 pagination 对象
        return {'data': db.session.scalars(query).all()}

class SOAGenerateAPI(MethodView):
    @serc_finance_bp.input(SOAGenerateSchema)
    @serc_finance_bp.output(SOAItemSchema, status_code=201)
    def post(self, data):
        """生成 L2 结算单 (from L1)"""
        soa = finance_service.generate_soa(data['l1_ids'])
        return {'data': soa}

class SOAConfirmAPI(MethodView):
    @serc_finance_bp.output(SOAItemSchema)
    def post(self, id):
        """确认 L2 结算单 (供应商对账完成)"""
        soa = finance_service.confirm_soa(id)
        return {'data': soa}

class SOAApproveAPI(MethodView):
    @serc_finance_bp.output(SOAItemSchema)
    def post(self, id):
        """批准 L2 结算单 (生成付款计划)"""
        soa = finance_service.approve_soa(id)
        return {'data': soa}

# --- L3: Payment & Pool ---

class PaymentPoolAPI(MethodView):
    @serc_finance_bp.output(PaymentPoolItemSchema(many=True))
    def get(self):
        """获取付款池 (待审批项)"""
        # 只显示待审批或待支付的
        stmt = select(FinPaymentPool).where(
            FinPaymentPool.status.in_([
                PaymentPoolStatus.PENDING_APPROVAL.value, 
                PaymentPoolStatus.PENDING_PAYMENT.value
            ])
        ).order_by(FinPaymentPool.priority.desc())
        
        return {'data': db.session.scalars(stmt).all()}

class PaymentCreateAPI(MethodView):
    @serc_finance_bp.input(PaymentCreateSchema)
    @serc_finance_bp.output(PaymentRequestSchema, status_code=201)
    def post(self, data):
        """生成 L3 付款单 (批准付款)"""
        payment_req = finance_service.execute_payment(
            pool_item_ids=data['pool_item_ids'],
            bank_account=data['bank_account']
        )
        return {'data': payment_req}

class PaymentTermsAPI(MethodView):
    @serc_finance_bp.output(PaymentTermSchema(many=True))
    def get(self):
        """获取付款条款列表"""
        terms = db.session.scalars(select(SysPaymentTerm).order_by(SysPaymentTerm.id)).all()
        return {'data': terms}

# Register Routes
serc_finance_bp.add_url_rule('/soa', view_func=SOAListAPI.as_view('soa_list'))
serc_finance_bp.add_url_rule('/soa/generate', view_func=SOAGenerateAPI.as_view('soa_generate'))
serc_finance_bp.add_url_rule('/soa/<int:id>/confirm', view_func=SOAConfirmAPI.as_view('soa_confirm'))
serc_finance_bp.add_url_rule('/soa/<int:id>/approve', view_func=SOAApproveAPI.as_view('soa_approve'))
serc_finance_bp.add_url_rule('/pool', view_func=PaymentPoolAPI.as_view('pool_list'))
serc_finance_bp.add_url_rule('/payment', view_func=PaymentCreateAPI.as_view('payment_create'))
serc_finance_bp.add_url_rule('/payment-terms', view_func=PaymentTermsAPI.as_view('payment_terms_list'))
