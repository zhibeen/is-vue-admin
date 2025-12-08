from apiflask import APIBlueprint
from apiflask.views import MethodView
from apiflask.fields import String, Integer, Dict, List, Nested, Raw
from sqlalchemy import select
from app.extensions import db
from app.models.product import SkuSuffix, SysTaxCategory, Product
from app.schemas.product.product import SkuSuffixSchema, TaxCategorySchema, NextSerialSchema, ProductPreviewResponseSchema
from app.services.sku_generator import get_next_serial_preview
from app.services.code_builder import CodeBuilderService
from app.security import auth
from app import codes

# Create Blueprint
aux_bp = APIBlueprint('product_aux', __name__, url_prefix='/products/aux', tag='Product-Auxiliary')

class ProductPreviewAPI(MethodView):
    decorators = [aux_bp.auth_required(auth)]
    
    @aux_bp.doc(summary='预览产品编码', description='根据参数预览 SPU Code 和 SKU 列表 (包含真实的流水号分配逻辑)')
    @aux_bp.input({
        'category_id': Integer(required=True),
        'spu_coding_metadata': Dict(required=True),
        'variants': List(Dict(keys=String, values=Raw), required=True)
    }, arg_name='data')
    @aux_bp.output(ProductPreviewResponseSchema)
    def post(self, data):
        """Preview product codes"""
        result = CodeBuilderService.preview_product_codes(
            category_id=data['category_id'],
            spu_metadata=data['spu_coding_metadata'],
            variants_specs=data['variants'] # expecting list of specs dicts
        )
        
        # Check for existing SPU Code
        spu_code = result.get('spu_code')
        if spu_code:
            existing = db.session.scalar(select(Product).filter_by(spu_code=spu_code))
            if existing:
                return {
                    'code': codes.PRODUCT_SPU_CODE_EXIST,
                    'message': f'SPU 编码 {spu_code} 已存在',
                    'data': result
                }
        
        return {'data': result}

class SkuSuffixListAPI(MethodView):
    decorators = [aux_bp.auth_required(auth)]
    
    @aux_bp.doc(summary='获取SKU后缀列表', description='获取所有SKU后缀定义。')
    @aux_bp.output(SkuSuffixSchema(many=True))
    def get(self):
        """List all SKU suffixes"""
        suffixes = db.session.scalars(select(SkuSuffix).order_by(SkuSuffix.code)).all()
        return {'data': suffixes}

class TaxCategoryListAPI(MethodView):
    decorators = [aux_bp.auth_required(auth)]
    
    @aux_bp.doc(summary='获取税收分类列表', description='获取所有标准税收分类。')
    @aux_bp.output(TaxCategorySchema(many=True))
    def get(self):
        """List all tax categories"""
        categories = db.session.scalars(select(SysTaxCategory).order_by(SysTaxCategory.code)).all()
        return {'data': categories}

class NextSerialAPI(MethodView):
    decorators = [aux_bp.auth_required(auth)]
    
    @aux_bp.doc(summary='获取下一个SKU流水号', description='根据前缀获取下一个可用的SKU流水号预览。')
    @aux_bp.input({'prefix': String(required=True)}, location='query', arg_name='query')
    @aux_bp.output(NextSerialSchema)
    def get(self, query):
        """Get next SKU serial preview"""
        prefix = query['prefix']
        serial = get_next_serial_preview(prefix)
        return {'data': {'serial': serial}}

# Register Routes
aux_bp.add_url_rule('/preview', view_func=ProductPreviewAPI.as_view('preview_codes'))
aux_bp.add_url_rule('/suffixes', view_func=SkuSuffixListAPI.as_view('suffix_list'))
aux_bp.add_url_rule('/tax-categories', view_func=TaxCategoryListAPI.as_view('tax_category_list'))
aux_bp.add_url_rule('/next-serial', view_func=NextSerialAPI.as_view('next_serial'))
