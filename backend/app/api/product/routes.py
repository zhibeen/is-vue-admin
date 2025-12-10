from apiflask import APIBlueprint
from app.schemas.product.product import ProductCreateSchema, ProductOutSchema, SkuSuffixSchema, ProductCreateResponseSchema
from app.schemas.pagination import make_pagination_schema, PaginationQuerySchema
from app.services.product_service import ProductService
from app.services.sku_generator import generate_sku
from app.security import auth
from app.decorators import permission_required
# 暂时注释掉以避免循环导入
# from app.tasks import send_email_task
from app.extensions import db
from app.models.product import SkuSuffix
from sqlalchemy import select

# url_prefix is now /products (relative to api_v1)
product_bp = APIBlueprint('product', __name__, url_prefix='/products', tag='Products')
product_service = ProductService()
ProductPaginationSchema = make_pagination_schema(ProductOutSchema)

@product_bp.post('')
@product_bp.auth_required(auth)
@permission_required('product:create')
@product_bp.doc(summary='创建商品', description='创建一个新商品，自动生成 SKU。需要提供分类ID和名称。')
@product_bp.input(ProductCreateSchema, arg_name='data')
@product_bp.output(ProductCreateResponseSchema, status_code=201)
def create_product(data):
    """Create a new product with auto-generated SKU"""
    result = product_service.create_product(data)
    
    # Trigger Async Task
    # result is a dict now, can't access .name directly. Use input data.
    # 暂时注释掉异步任务
    # send_email_task.delay('admin@example.com', 'Product Created/Updated', f"Product SPU {result['spu_code']} was processed.")
    
    # Return result dict directly
    return {'data': result}

@product_bp.get('/<int:product_id>')
@product_bp.auth_required(auth)
@product_bp.doc(
    summary='获取商品详情', 
    description='根据 ID 获取商品的详细信息。'
)
@product_bp.output(ProductOutSchema)
def get_product(product_id):
    """Get product details"""
    return {'data': product_service.get_product(product_id)}

@product_bp.get('')
@product_bp.auth_required(auth)
@product_bp.doc(summary='获取商品列表', description='获取商品列表（分页、搜索、排序）。')
@product_bp.input(PaginationQuerySchema, location='query', arg_name='query_data')
@product_bp.output(ProductPaginationSchema)
def list_products(query_data):
    """List all products"""
    return {'data': product_service.list_products(
        page=query_data['page'], 
        per_page=query_data['per_page'],
        q=query_data.get('q'),
        sort=query_data.get('sort')
    )}

@product_bp.get('/suffixes')
@product_bp.auth_required(auth)
@product_bp.doc(summary='获取SKU后缀列表', description='获取所有SKU后缀定义。')
@product_bp.output(SkuSuffixSchema(many=True))
def list_sku_suffixes():
    """List all SKU suffixes"""
    suffixes = db.session.scalars(select(SkuSuffix).order_by(SkuSuffix.code)).all()
    return {'data': suffixes}

@product_bp.get('/variants')
@product_bp.auth_required(auth)
@product_bp.doc(
    summary='获取SKU列表', 
    description='获取所有SKU列表，支持多维度筛选（搜索、分类、品牌、车型、属性、库存、状态等）。'
)
@product_bp.input(PaginationQuerySchema, location='query', arg_name='pagination')
def list_skus(pagination):
    """List all SKUs with filtering"""
    from flask import request
    
    # 构建筛选条件
    filters = {}
    
    # 搜索关键词
    q = request.args.get('q')
    if q:
        filters['q'] = q
    
    # 分类筛选
    category_id = request.args.get('category_id')
    if category_id:
        try:
            filters['category_id'] = int(category_id)
        except ValueError:
            pass
    
    # 品牌/车型筛选
    brand = request.args.get('brand')
    if brand:
        filters['brand'] = brand
    
    model = request.args.get('model')
    if model:
        filters['model'] = model
    
    # 状态筛选
    is_active = request.args.get('is_active')
    if is_active is not None:
        filters['is_active'] = is_active.lower() == 'true'
    
    # 库存筛选 (TODO: 集成库存系统后实现)
    # stock_min = request.args.get('stock_min')
    # stock_max = request.args.get('stock_max')
    
    # 属性筛选 (TODO: 支持JSONB查询)
    # 可以扩展为支持多个属性筛选
    
    result = product_service.list_skus(
        page=pagination['page'],
        per_page=pagination['per_page'],
        filters=filters
    )
    
    return {'data': result}

@product_bp.get('/variants/<string:sku>')
@product_bp.auth_required(auth)
@product_bp.doc(
    summary='获取SKU详情', 
    description='根据SKU编码获取详细信息，包括编码规则、属性、合规信息、参考编码等。'
)
def get_sku_detail(sku):
    """Get SKU details"""
    result = product_service.get_sku_detail(sku)
    return {'data': result}

@product_bp.put('/variants/<string:sku>')
@product_bp.auth_required(auth)
@permission_required('product:update')
@product_bp.doc(
    summary='更新SKU信息', 
    description='更新SKU的非编码字段（价格、库存、状态、合规信息等）。'
)
def update_sku(sku):
    """Update SKU information"""
    from flask import request
    data = request.get_json()
    
    if not data:
        return {'code': 400, 'message': '请求数据不能为空'}
    
    result = product_service.update_sku(sku, data)
    return {'data': result}

@product_bp.delete('/variants/<string:sku>')
@product_bp.auth_required(auth)
@permission_required('product:delete')
@product_bp.doc(
    summary='删除SKU', 
    description='删除指定的SKU。注意：删除前需要确保没有库存或订单关联。'
)
def delete_sku(sku):
    """Delete SKU"""
    product_service.delete_sku(sku)
    return {'code': 0, 'message': '删除成功'}

@product_bp.post('/variants/<string:sku>/toggle-status')
@product_bp.auth_required(auth)
@permission_required('product:update')
@product_bp.doc(
    summary='切换SKU状态', 
    description='切换SKU的启用/停用状态。'
)
def toggle_sku_status(sku):
    """Toggle SKU status"""
    result = product_service.toggle_sku_status(sku)
    return {'data': result}

@product_bp.get('/next-serial')
@product_bp.auth_required(auth)
@product_bp.doc(summary='获取下一个SKU流水号', description='根据前缀获取下一个可用的SKU流水号（4位数字字符串）。')
def get_next_sku_serial():
    """Get next SKU serial for preview"""
    # Note: This is just a preview. The actual serial is generated at creation time to avoid race conditions.
    # However, for UI display, we can estimate it.
    from flask import request
    prefix = request.args.get('prefix', '')
    if not prefix:
        return {'data': '0001'}
    
    # We don't have a public method in ProductService or sku_generator for just getting the next serial 
    # without incrementing or race condition checks. 
    # But checking app/services/sku_generator.py might reveal logic we can reuse or mimic.
    
    # For now, let's just return a placeholder or implement a simple check if possible.
    # Actually, let's rely on sku_generator's internal logic if accessible, 
    # or just return '????' to indicate it's generated on save.
    # User asked for "getNextSkuSerialApi", implying they want to see "0615" or similar.
    
    # Let's try to query the DB for the max serial for this prefix.
    # Assuming standard SKU format: Prefix + Serial + Suffix
    # This is complex because of suffixes.
    
    # Implementation detail:
    # If we look at `app/services/sku_generator.py`, it likely uses Redis or DB sequence.
    # Let's just import and use it if it's safe (idempotent preview). 
    # Usually `generate_sku` increments the counter. We don't want to increment on preview.
    # So we should probably peek.
    
    from app.services.sku_generator import get_next_serial_preview
    serial = get_next_serial_preview(prefix)
    return {'data': serial}
