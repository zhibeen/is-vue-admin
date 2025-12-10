from apiflask import APIBlueprint, abort
from apiflask.views import MethodView
from app.schemas.serc.foundation import (
    CompanySimpleSchema, CompanyDetailSchema, HSCodeSimpleSchema,
    CompanyCreateSchema, CompanyUpdateSchema, TaxCategorySchema,
    HSCodeCreateSchema, HSCodeUpdateSchema
)
from app.models.serc.foundation import SysCompany, SysHSCode
from app.models.product import SysTaxCategory
from app.extensions import db
from sqlalchemy import select

serc_foundation_bp = APIBlueprint('serc_foundation', __name__, url_prefix='/foundation', tag='SERC-基础数据')

class CompanyListAPI(MethodView):
    @serc_foundation_bp.doc(summary='获取采购主体列表', description='获取所有采购主体（公司）列表')
    @serc_foundation_bp.output(CompanySimpleSchema(many=True))
    def get(self):
        """获取采购主体列表"""
        companies = db.session.scalars(select(SysCompany).order_by(SysCompany.id)).all()
        return {'data': companies}

    @serc_foundation_bp.doc(summary='创建采购主体', description='创建新的采购主体（公司）')
    @serc_foundation_bp.input(CompanyCreateSchema, arg_name='data')
    @serc_foundation_bp.output(CompanyDetailSchema, status_code=201)
    def post(self, data):
        """创建采购主体"""
        company = SysCompany(**data)
        db.session.add(company)
        db.session.commit()
        return {'data': company}

class CompanyDetailAPI(MethodView):
    @serc_foundation_bp.doc(summary='获取采购主体详情', description='根据ID获取采购主体详细信息')
    @serc_foundation_bp.output(CompanyDetailSchema)
    def get(self, company_id):
        """获取采购主体详情"""
        company = db.session.get(SysCompany, company_id)
        if not company:
            abort(404, 'Not found')
        return {'data': company}

    @serc_foundation_bp.doc(summary='更新采购主体', description='更新采购主体信息')
    @serc_foundation_bp.input(CompanyUpdateSchema, arg_name='data')
    @serc_foundation_bp.output(CompanyDetailSchema)
    def put(self, company_id, data):
        """更新采购主体"""
        company = db.session.get(SysCompany, company_id)
        if not company:
            abort(404, 'Not found')
        
        for key, value in data.items():
            setattr(company, key, value)
        
        db.session.commit()
        return {'data': company}

    @serc_foundation_bp.doc(summary='删除采购主体', description='删除指定的采购主体')
    def delete(self, company_id):
        """删除采购主体"""
        company = db.session.get(SysCompany, company_id)
        if company:
            db.session.delete(company)
            db.session.commit()
        return None

class HSCodeListAPI(MethodView):
    @serc_foundation_bp.output(HSCodeSimpleSchema(many=True))
    def get(self):
        """获取海关编码列表"""
        codes = db.session.scalars(select(SysHSCode).order_by(SysHSCode.code)).all()
        return {'data': codes}
        
    @serc_foundation_bp.doc(summary='创建HS编码', description='创建新的海关编码')
    @serc_foundation_bp.input(HSCodeCreateSchema, arg_name='data')
    @serc_foundation_bp.output(HSCodeSimpleSchema, status_code=201)
    def post(self, data):
        """创建HS编码"""
        # Check if code exists
        existing = db.session.scalar(select(SysHSCode).filter_by(code=data['code']))
        if existing:
            abort(400, 'HS Code already exists')
            
        hscode = SysHSCode(**data)
        db.session.add(hscode)
        db.session.commit()
        return {'data': hscode}

class HSCodeDetailAPI(MethodView):
    @serc_foundation_bp.doc(summary='更新HS编码', description='更新海关编码信息')
    @serc_foundation_bp.input(HSCodeUpdateSchema, arg_name='data')
    @serc_foundation_bp.output(HSCodeSimpleSchema)
    def put(self, hscode_id, data):
        """更新HS编码"""
        hscode = db.session.get(SysHSCode, hscode_id)
        if not hscode:
            abort(404, 'HS Code not found')
        
        # Check code uniqueness if changing code
        if 'code' in data and data['code'] != hscode.code:
             existing = db.session.scalar(select(SysHSCode).filter_by(code=data['code']))
             if existing:
                 abort(400, 'HS Code already exists')
        
        for key, value in data.items():
            setattr(hscode, key, value)
            
        db.session.commit()
        return {'data': hscode}

    @serc_foundation_bp.doc(summary='删除HS编码', description='删除指定的海关编码')
    def delete(self, hscode_id):
        """删除HS编码"""
        hscode = db.session.get(SysHSCode, hscode_id)
        if hscode:
            db.session.delete(hscode)
            db.session.commit()
        return None

class TaxCategoryListAPI(MethodView):
    @serc_foundation_bp.output(TaxCategorySchema(many=True))
    def get(self):
        """获取税收分类列表"""
        # order by code
        cats = db.session.scalars(select(SysTaxCategory).order_by(SysTaxCategory.code)).all()
        return {'data': cats}

serc_foundation_bp.add_url_rule('/companies', view_func=CompanyListAPI.as_view('company_list'))
serc_foundation_bp.add_url_rule('/companies/<int:company_id>', view_func=CompanyDetailAPI.as_view('company_detail'))
serc_foundation_bp.add_url_rule('/hscodes', view_func=HSCodeListAPI.as_view('hscode_list'))
serc_foundation_bp.add_url_rule('/hscodes/<int:hscode_id>', view_func=HSCodeDetailAPI.as_view('hscode_detail'))
serc_foundation_bp.add_url_rule('/tax-categories', view_func=TaxCategoryListAPI.as_view('tax_category_list'))
