from apiflask import APIBlueprint, abort
from apiflask.views import MethodView
from sqlalchemy import select
from app.extensions import db
from app.models.product.rule import ProductBusinessRule
from app.schemas.product.rule import ProductBusinessRuleSchema
from app.security import auth
# from app.models.system import SysDictItem, SysDict # 移除对字典的依赖

rule_bp = APIBlueprint('product_rule', __name__, url_prefix='/product/rules', tag='Product Rules')

class ProductBusinessRuleListAPI(MethodView):
    decorators = [rule_bp.auth_required(auth)]
    
    @rule_bp.doc(summary='获取业务规则列表')
    @rule_bp.output(ProductBusinessRuleSchema(many=True))
    def get(self):
        """List all business rules"""
        # 直接从数据库读取规则，不再同步字典
        rules = db.session.scalars(select(ProductBusinessRule).order_by(ProductBusinessRule.id)).all()
        return {'data': rules}

    @rule_bp.doc(summary='创建业务规则')
    @rule_bp.input(ProductBusinessRuleSchema, arg_name='data')
    @rule_bp.output(ProductBusinessRuleSchema)
    def post(self, data):
        """Create a new business rule"""
        # 检查业务类型是否存在
        if db.session.scalar(select(ProductBusinessRule).where(ProductBusinessRule.business_type == data['business_type'])):
            abort(400, 'Business type already exists')
            
        rule = ProductBusinessRule(**data)
        db.session.add(rule)
        db.session.commit()
        return {'data': rule}

class ProductBusinessRuleDetailAPI(MethodView):
    decorators = [rule_bp.auth_required(auth)]
    
    @rule_bp.doc(summary='更新业务规则')
    @rule_bp.input(ProductBusinessRuleSchema(partial=True), arg_name='data')
    @rule_bp.output(ProductBusinessRuleSchema)
    def put(self, rule_id, data):
        rule = db.session.get(ProductBusinessRule, rule_id)
        if not rule:
            abort(404)
            
        for k, v in data.items():
            setattr(rule, k, v)
        db.session.commit()
        return {'data': rule}

    @rule_bp.doc(summary='删除业务规则')
    def delete(self, rule_id):
        """Delete a business rule"""
        rule = db.session.get(ProductBusinessRule, rule_id)
        if not rule:
            abort(404)
        
        # TODO: 检查是否有产品或分类正在使用该规则，如果有则禁止删除
        # if rule.in_use: ...
        
        db.session.delete(rule)
        db.session.commit()
        return None

# Register Routes
rule_bp.add_url_rule('', view_func=ProductBusinessRuleListAPI.as_view('rule_list'))
rule_bp.add_url_rule('/<int:rule_id>', view_func=ProductBusinessRuleDetailAPI.as_view('rule_detail'))
