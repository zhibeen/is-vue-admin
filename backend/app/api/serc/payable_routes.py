"""财务应付单API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from app.security import auth
from app.decorators import permission_required
from app.schemas.serc.payable import (
    FinPayableSchema,
    CreatePayableSchema,
    ApprovalSchema,
    AddToPoolSchema,
    MarkPaidSchema,
    FinPayableDetailSchema,
    FinPaymentPoolSchema,
    CreatePaymentPoolSchema
)
from app.schemas.pagination import PaginationQuerySchema, make_pagination_schema
from app.services.serc.payable_service import PayableService
from app.models.serc.payable import FinPayable, FinPaymentPool
from app.extensions import db
from sqlalchemy import or_


payable_bp = APIBlueprint(
    'finance_payables',
    __name__,
    url_prefix='/finance/payables',
    tag='财务应付账款管理'
)


class FinPayableListAPI(MethodView):
    """应付单列表API"""
    decorators = [payable_bp.auth_required(auth)]
    
    @payable_bp.doc(
        summary='获取应付单列表',
        description='获取财务应付单列表，支持按来源类型、状态、收款方筛选'
    )
    @payable_bp.input(PaginationQuerySchema, location='query', arg_name='pagination')
    @payable_bp.output(make_pagination_schema(FinPayableSchema))
    @permission_required('finance:payable:view')
    def get(self, pagination):
        """获取应付单列表"""
        page = pagination['page']
        per_page = pagination['per_page']
        
        query = FinPayable.query
        
        # 搜索过滤（应付单号、收款方名称）
        if pagination.get('q'):
            q = f"%{pagination['q']}%"
            query = query.filter(
                or_(
                    FinPayable.payable_no.ilike(q),
                    FinPayable.payee_name.ilike(q)
                )
            )
        
        # 来源类型过滤
        if pagination.get('source_type'):
            query = query.filter(FinPayable.source_type == pagination['source_type'])
        
        # 状态过滤
        if pagination.get('status'):
            query = query.filter(FinPayable.status == pagination['status'])
        
        # 收款方过滤
        if pagination.get('payee_id'):
            query = query.filter(FinPayable.payee_id == pagination['payee_id'])
        
        # 付款池过滤
        if pagination.get('pool_id'):
            query = query.filter(FinPayable.payment_pool_id == pagination['pool_id'])
        
        # 日期范围过滤
        if pagination.get('start_date'):
            query = query.filter(FinPayable.due_date >= pagination['start_date'])
        if pagination.get('end_date'):
            query = query.filter(FinPayable.due_date <= pagination['end_date'])
        
        # 排序
        query = query.order_by(FinPayable.created_at.desc())
        
        # 分页
        pagination_obj = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'data': {
                'items': pagination_obj.items,
                'total': pagination_obj.total,
                'page': page,
                'per_page': per_page
            }
        }
    
    @payable_bp.doc(
        summary='创建应付单',
        description='创建财务应付单（供其他业务模块调用）'
    )
    @payable_bp.input(CreatePayableSchema, arg_name='data')
    @payable_bp.output(FinPayableSchema, status_code=201)
    @permission_required('finance:payable:create')
    def post(self, data):
        """创建应付单"""
        user_id = get_jwt_identity()
        payable = PayableService.create_payable(data, created_by=user_id)
        return {'data': payable}


class FinPayableItemAPI(MethodView):
    """应付单详情API"""
    decorators = [payable_bp.auth_required(auth)]
    
    @payable_bp.doc(summary='获取应付单详情', description='获取应付单详情，包含审批人、付款池等信息')
    @payable_bp.output(FinPayableDetailSchema)
    @permission_required('finance:payable:view')
    def get(self, payable_id):
        """获取应付单详情"""
        from app.errors import BusinessError
        payable = PayableService.get_payable_by_id(payable_id)
        if not payable:
            raise BusinessError('应付单不存在', code=404)
        return {'data': payable}


class FinPayableApprovalAPI(MethodView):
    """应付单审批API"""
    decorators = [payable_bp.auth_required(auth)]
    
    @payable_bp.doc(
        summary='审批应付单',
        description='财务主管审批应付单，支持批准/驳回，批准后可选择是否立即加入付款池'
    )
    @payable_bp.input(ApprovalSchema, arg_name='data')
    @payable_bp.output(FinPayableSchema)
    @permission_required('finance:payable:approve')
    def post(self, payable_id, data):
        """审批应付单"""
        user_id = get_jwt_identity()
        payable = PayableService.approve_payable(
            payable_id=payable_id,
            action=data['action'],
            approved_by=user_id,
            rejection_reason=data.get('rejection_reason'),
            add_to_pool=data.get('add_to_pool', False),
            pool_id=data.get('pool_id')
        )
        return {'data': payable}


class FinPayableAddToPoolAPI(MethodView):
    """应付单加入付款池API"""
    decorators = [payable_bp.auth_required(auth)]
    
    @payable_bp.doc(
        summary='将应付单加入付款池',
        description='将已批准的应付单加入指定的付款池'
    )
    @payable_bp.input(AddToPoolSchema, arg_name='data')
    @payable_bp.output(FinPayableSchema)
    @permission_required('finance:payable:manage')
    def post(self, payable_id, data):
        """将应付单加入付款池"""
        payable = PayableService.add_payable_to_pool(payable_id, data['pool_id'])
        return {'data': payable}


class FinPayableMarkPaidAPI(MethodView):
    """应付单标记已付款API"""
    decorators = [payable_bp.auth_required(auth)]
    
    @payable_bp.doc(
        summary='标记应付单为已付款',
        description='出纳执行付款后标记应付单为已付款，支持部分付款'
    )
    @payable_bp.input(MarkPaidSchema, arg_name='data')
    @payable_bp.output(FinPayableSchema)
    @permission_required('finance:payable:pay')
    def post(self, payable_id, data):
        """标记应付单为已付款"""
        payable = PayableService.mark_as_paid(
            payable_id=payable_id,
            paid_amount=data['paid_amount'],
            paid_at=data.get('paid_at'),
            payment_voucher_id=data.get('payment_voucher_id')
        )
        return {'data': payable}


# 注册应付单路由
payable_bp.add_url_rule(
    '',
    view_func=FinPayableListAPI.as_view('payable_list'),
    methods=['GET', 'POST']
)

payable_bp.add_url_rule(
    '/<int:payable_id>',
    view_func=FinPayableItemAPI.as_view('payable_item'),
    methods=['GET']
)

payable_bp.add_url_rule(
    '/<int:payable_id>/approve',
    view_func=FinPayableApprovalAPI.as_view('payable_approve'),
    methods=['POST']
)

payable_bp.add_url_rule(
    '/<int:payable_id>/add-to-pool',
    view_func=FinPayableAddToPoolAPI.as_view('payable_add_to_pool'),
    methods=['POST']
)

payable_bp.add_url_rule(
    '/<int:payable_id>/mark-paid',
    view_func=FinPayableMarkPaidAPI.as_view('payable_mark_paid'),
    methods=['POST']
)


# ==================== 付款池 API ==================== #

payment_pool_bp = APIBlueprint(
    'finance_payment_pools',
    __name__,
    url_prefix='/finance/payment-pools',
    tag='财务付款池管理'
)


class FinPaymentPoolListAPI(MethodView):
    """付款池列表API"""
    decorators = [payment_pool_bp.auth_required(auth)]
    
    @payment_pool_bp.doc(summary='获取付款池列表', description='获取财务付款池列表')
    @payment_pool_bp.input(PaginationQuerySchema, location='query', arg_name='pagination')
    @payment_pool_bp.output(make_pagination_schema(FinPaymentPoolSchema))
    @permission_required('finance:pool:view')
    def get(self, pagination):
        """获取付款池列表"""
        page = pagination['page']
        per_page = pagination['per_page']
        
        query = FinPaymentPool.query
        
        # 搜索过滤
        if pagination.get('q'):
            q = f"%{pagination['q']}%"
            query = query.filter(
                or_(
                    FinPaymentPool.pool_no.ilike(q),
                    FinPaymentPool.pool_name.ilike(q)
                )
            )
        
        # 状态过滤
        if pagination.get('status'):
            query = query.filter(FinPaymentPool.status == pagination['status'])
        
        # 排序
        query = query.order_by(FinPaymentPool.created_at.desc())
        
        # 分页
        pagination_obj = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'data': {
                'items': pagination_obj.items,
                'total': pagination_obj.total,
                'page': page,
                'per_page': per_page
            }
        }
    
    @payment_pool_bp.doc(summary='创建付款池', description='创建新的付款池')
    @payment_pool_bp.input(CreatePaymentPoolSchema, arg_name='data')
    @payment_pool_bp.output(FinPaymentPoolSchema, status_code=201)
    @permission_required('finance:pool:create')
    def post(self, data):
        """创建付款池"""
        # TODO: 实现创建付款池的服务方法
        pass


# 注册付款池路由
payment_pool_bp.add_url_rule(
    '',
    view_func=FinPaymentPoolListAPI.as_view('pool_list'),
    methods=['GET', 'POST']
)

