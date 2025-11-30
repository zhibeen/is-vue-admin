from apiflask import APIBlueprint, abort
from apiflask.views import MethodView
from app.schemas.purchase.supplier import (
    SupplierSimpleSchema, SupplierDetailSchema, SupplierCreateSchema, SupplierUpdateSchema,
    SupplierSearchSchema
)
from app.schemas.pagination import make_pagination_schema
from app.models.purchase.supplier import SysSupplier
from app.extensions import db
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from math import ceil

purchase_supplier_bp = APIBlueprint('purchase_supplier', __name__, tag='Purchase-供应商')

class SupplierListAPI(MethodView):
    @purchase_supplier_bp.doc(summary='获取供应商列表', description='支持分页和搜索的供应商列表')
    @purchase_supplier_bp.input(SupplierSearchSchema, location='query', arg_name='pagination')
    @purchase_supplier_bp.output(make_pagination_schema(SupplierSimpleSchema))
    def get(self, pagination):
        """获取供应商列表（分页）"""
        page = pagination['page']
        per_page = pagination['per_page']
        q = pagination.get('q')
        supplier_type = pagination.get('supplier_type')
        status = pagination.get('status')
        
        # 构建查询
        stmt = select(SysSupplier).options(
            joinedload(SysSupplier.payment_term)  # 预加载付款条款
        )
        
        # 搜索过滤（支持代码、名称、简称）
        if q:
            stmt = stmt.where(
                or_(
                    SysSupplier.code.ilike(f'%{q}%'),
                    SysSupplier.name.ilike(f'%{q}%'),
                    SysSupplier.short_name.ilike(f'%{q}%')
                )
            )
            
        # 精确过滤
        if supplier_type:
            stmt = stmt.where(SysSupplier.supplier_type == supplier_type)
            
        if status:
            stmt = stmt.where(SysSupplier.status == status)
        
        # 排序
        stmt = stmt.order_by(SysSupplier.id.desc())
        
        # 计算总数
        total = db.session.scalar(
            select(db.func.count()).select_from(stmt.subquery())
        )
        
        # 分页
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        
        # 执行查询
        suppliers = db.session.scalars(stmt).all()
        
        return {
            'data': {
                'items': suppliers,
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': ceil(total / per_page) if per_page > 0 else 0
            }
        }

    @purchase_supplier_bp.doc(summary='创建供应商', description='创建新的供应商')
    @purchase_supplier_bp.input(SupplierCreateSchema, arg_name='data')
    @purchase_supplier_bp.output(SupplierDetailSchema, status_code=201)
    def post(self, data):
        """创建供应商"""
        supplier = SysSupplier(**data)
        db.session.add(supplier)
        db.session.commit()
        return {'data': supplier}

class SupplierDetailAPI(MethodView):
    @purchase_supplier_bp.doc(summary='获取供应商详情', description='根据ID获取供应商详细信息')
    @purchase_supplier_bp.output(SupplierDetailSchema)
    def get(self, supplier_id):
        """获取供应商详情"""
        supplier = db.session.get(SysSupplier, supplier_id)
        if not supplier:
            abort(404, 'Not found')
        return {'data': supplier}

    @purchase_supplier_bp.doc(summary='更新供应商', description='更新供应商信息')
    @purchase_supplier_bp.input(SupplierUpdateSchema, arg_name='data')
    @purchase_supplier_bp.output(SupplierDetailSchema)
    def put(self, supplier_id, data):
        """更新供应商"""
        supplier = db.session.get(SysSupplier, supplier_id)
        if not supplier:
            abort(404, 'Not found')
        
        for key, value in data.items():
            setattr(supplier, key, value)
        
        db.session.commit()
        return {'data': supplier}

    @purchase_supplier_bp.doc(summary='删除供应商', description='删除指定的供应商')
    @purchase_supplier_bp.output({}, status_code=204)
    def delete(self, supplier_id):
        """删除供应商"""
        supplier = db.session.get(SysSupplier, supplier_id)
        if supplier:
            db.session.delete(supplier)
            db.session.commit()
        return None

purchase_supplier_bp.add_url_rule('/suppliers', view_func=SupplierListAPI.as_view('supplier_list'))
purchase_supplier_bp.add_url_rule('/suppliers/<int:supplier_id>', view_func=SupplierDetailAPI.as_view('supplier_detail'))
