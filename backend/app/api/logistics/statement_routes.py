"""物流对账单API路由"""
from apiflask import APIBlueprint
from apiflask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from app.security import auth
from app.decorators import permission_required
from app.schemas.logistics.statement import (
    LogisticsStatementSchema,
    CreateStatementSchema,
    UpdateStatementSchema,
    AddServiceToStatementSchema,
    StatementSubmitResponseSchema,
    LogisticsStatementDetailSchema
)
from app.schemas.pagination import PaginationQuerySchema, make_pagination_schema
from app.services.logistics.statement_service import StatementService
from app.models.logistics.logistics_statement import LogisticsStatement
from app.extensions import db
from sqlalchemy import or_, and_


statement_bp = APIBlueprint(
    'logistics_statements',
    __name__,
    url_prefix='/logistics/statements',
    tag='物流对账管理'
)


class LogisticsStatementListAPI(MethodView):
    """物流对账单列表API"""
    decorators = [statement_bp.auth_required(auth)]
    
    @statement_bp.doc(
        summary='获取对账单列表',
        description='获取物流对账单列表，支持按物流商、状态、周期筛选'
    )
    @statement_bp.input(PaginationQuerySchema, location='query', arg_name='pagination')
    @statement_bp.output(make_pagination_schema(LogisticsStatementSchema))
    def get(self, pagination):
        """获取对账单列表"""
        page = pagination['page']
        per_page = pagination['per_page']
        
        query = LogisticsStatement.query
        
        # 搜索过滤（对账单号、物流商名称）
        if pagination.get('q'):
            q = f"%{pagination['q']}%"
            query = query.join(LogisticsStatement.logistics_provider).filter(
                or_(
                    LogisticsStatement.statement_no.ilike(q),
                    LogisticsStatement.logistics_provider.has(provider_name=q)
                )
            )
        
        # 状态过滤
        if pagination.get('status'):
            query = query.filter(LogisticsStatement.status == pagination['status'])
        
        # 物流商过滤
        if pagination.get('provider_id'):
            query = query.filter(LogisticsStatement.logistics_provider_id == pagination['provider_id'])
        
        # 日期范围过滤
        if pagination.get('start_date'):
            query = query.filter(LogisticsStatement.statement_period_start >= pagination['start_date'])
        if pagination.get('end_date'):
            query = query.filter(LogisticsStatement.statement_period_end <= pagination['end_date'])
        
        # 排序
        query = query.order_by(LogisticsStatement.created_at.desc())
        
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
    
    @statement_bp.doc(summary='创建对账单（草稿）', description='创建物流对账单草稿')
    @statement_bp.input(CreateStatementSchema, arg_name='data')
    @statement_bp.output(LogisticsStatementSchema, status_code=201)
    @permission_required('logistics:statement:create')
    def post(self, data):
        """创建对账单草稿"""
        user_id = get_jwt_identity()
        statement = StatementService.create_draft_statement(data, created_by=user_id)
        return {'data': statement}


class LogisticsStatementItemAPI(MethodView):
    """对账单详情API"""
    decorators = [statement_bp.auth_required(auth)]
    
    @statement_bp.doc(summary='获取对账单详情', description='获取对账单详情，包含关联的物流服务')
    @statement_bp.output(LogisticsStatementDetailSchema)
    def get(self, statement_id):
        """获取对账单详情"""
        from app.errors import BusinessError
        statement = StatementService.get_statement_by_id(statement_id)
        if not statement:
            raise BusinessError('对账单不存在', code=404)
        return {'data': statement}
    
    @statement_bp.doc(summary='更新对账单', description='更新对账单信息（仅草稿状态可修改）')
    @statement_bp.input(UpdateStatementSchema, arg_name='data')
    @statement_bp.output(LogisticsStatementSchema)
    @permission_required('logistics:statement:update')
    def put(self, statement_id, data):
        """更新对账单"""
        statement = StatementService.update_statement(statement_id, data)
        return {'data': statement}
    
    @statement_bp.doc(summary='删除对账单', description='删除对账单（仅草稿状态可删除）')
    @permission_required('logistics:statement:delete')
    def delete(self, statement_id):
        """删除对账单"""
        StatementService.delete_statement(statement_id)
        return {'data': {'success': True}}


class LogisticsStatementConfirmAPI(MethodView):
    """确认对账单API"""
    decorators = [statement_bp.auth_required(auth)]
    
    @statement_bp.doc(
        summary='确认对账单（物流主管）',
        description='物流主管确认对账单，确认后可提交财务'
    )
    @statement_bp.output(LogisticsStatementSchema)
    @permission_required('logistics:statement:confirm')
    def post(self, statement_id):
        """确认对账单"""
        user_id = get_jwt_identity()
        statement = StatementService.confirm_statement(statement_id, confirmed_by=user_id)
        return {'data': statement}


class LogisticsStatementSubmitAPI(MethodView):
    """提交对账单到财务API"""
    decorators = [statement_bp.auth_required(auth)]
    
    @statement_bp.doc(
        summary='提交对账单到财务审批',
        description='将已确认的对账单提交给财务模块，自动生成应付单'
    )
    @statement_bp.output(StatementSubmitResponseSchema)
    @permission_required('logistics:statement:submit')
    def post(self, statement_id):
        """提交对账单到财务"""
        result = StatementService.submit_to_finance(statement_id)
        return {'data': result}


class LogisticsStatementAddServiceAPI(MethodView):
    """添加物流服务到对账单API"""
    decorators = [statement_bp.auth_required(auth)]
    
    @statement_bp.doc(
        summary='添加物流服务到对账单',
        description='将物流服务记录添加到对账单中'
    )
    @statement_bp.input(AddServiceToStatementSchema, arg_name='data')
    @statement_bp.output(LogisticsStatementSchema)
    @permission_required('logistics:statement:update')
    def post(self, statement_id, data):
        """添加物流服务到对账单"""
        StatementService.add_service_to_statement(
            statement_id=statement_id,
            service_id=data['service_id'],
            reconciled_amount=data.get('reconciled_amount')
        )
        statement = StatementService.get_statement_by_id(statement_id)
        return {'data': statement}


class LogisticsStatementRemoveServiceAPI(MethodView):
    """从对账单移除物流服务API"""
    decorators = [statement_bp.auth_required(auth)]
    
    @statement_bp.doc(
        summary='从对账单移除物流服务',
        description='将物流服务记录从对账单中移除'
    )
    @statement_bp.output(LogisticsStatementSchema)
    @permission_required('logistics:statement:update')
    def delete(self, statement_id, service_id):
        """从对账单移除物流服务"""
        StatementService.remove_service_from_statement(statement_id, service_id)
        statement = StatementService.get_statement_by_id(statement_id)
        return {'data': statement}


# 注册路由
statement_bp.add_url_rule(
    '',
    view_func=LogisticsStatementListAPI.as_view('statement_list'),
    methods=['GET', 'POST']
)

statement_bp.add_url_rule(
    '/<int:statement_id>',
    view_func=LogisticsStatementItemAPI.as_view('statement_item'),
    methods=['GET', 'PUT', 'DELETE']
)

statement_bp.add_url_rule(
    '/<int:statement_id>/confirm',
    view_func=LogisticsStatementConfirmAPI.as_view('statement_confirm'),
    methods=['POST']
)

statement_bp.add_url_rule(
    '/<int:statement_id>/submit',
    view_func=LogisticsStatementSubmitAPI.as_view('statement_submit'),
    methods=['POST']
)

statement_bp.add_url_rule(
    '/<int:statement_id>/services',
    view_func=LogisticsStatementAddServiceAPI.as_view('statement_add_service'),
    methods=['POST']
)

statement_bp.add_url_rule(
    '/<int:statement_id>/services/<int:service_id>',
    view_func=LogisticsStatementRemoveServiceAPI.as_view('statement_remove_service'),
    methods=['DELETE']
)

