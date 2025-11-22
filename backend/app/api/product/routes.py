from apiflask import APIBlueprint
from app.schemas.product import ProductCreateSchema, ProductOutSchema
from app.schemas.pagination import make_pagination_schema, PaginationQuerySchema
from app.services.product_service import ProductService
from app.security import auth
from app.decorators import permission_required
from app.tasks import send_email_task

# url_prefix is now /products (relative to api_v1)
product_bp = APIBlueprint('product', __name__, url_prefix='/products', tag='Products')
product_service = ProductService()
ProductPaginationSchema = make_pagination_schema(ProductOutSchema)

@product_bp.post('')
@product_bp.auth_required(auth)
@permission_required('product:create')
@product_bp.doc(summary='创建商品', description='创建一个新商品，自动生成 SKU。需要提供分类ID和名称。')
@product_bp.input(ProductCreateSchema, arg_name='data')
@product_bp.output(ProductOutSchema, status_code=201)
def create_product(data):
    """Create a new product with auto-generated SKU"""
    product = product_service.create_product(data)
    
    # Trigger Async Task
    send_email_task.delay('admin@example.com', 'New Product Created', f'Product {product.name} was created.')
    
    return product

@product_bp.get('/<int:product_id>')
@product_bp.auth_required(auth)
@product_bp.doc(
    summary='获取商品详情', 
    description='根据 ID 获取商品的详细信息。'
)
@product_bp.output(ProductOutSchema)
def get_product(product_id):
    """Get product details"""
    return product_service.get_product(product_id)

@product_bp.get('')
@product_bp.auth_required(auth)
@product_bp.doc(summary='获取商品列表', description='获取商品列表（分页、搜索、排序）。')
@product_bp.input(PaginationQuerySchema, location='query', arg_name='query_data')
@product_bp.output(ProductPaginationSchema)
def list_products(query_data):
    """List all products"""
    return product_service.list_products(
        page=query_data['page'], 
        per_page=query_data['per_page'],
        q=query_data.get('q'),
        sort=query_data.get('sort')
    )
