from apiflask import APIBlueprint, abort
from sqlalchemy import select
from app.extensions import db
from app.models.category import Category, AttributeDefinition, CategoryAttribute
from app.schemas.product import CategoryTreeSchema, CategoryDetailSchema, AttributeDefinitionSchema, CategoryBaseSchema
from app.security import auth
from app.decorators import permission_required

# url_prefix is now /categories (relative to api_v1)
category_bp = APIBlueprint('category', __name__, url_prefix='/categories', tag='Categories')

@category_bp.get('/tree')
@category_bp.auth_required(auth)
@category_bp.doc(summary='获取分类树', description='获取完整的商品分类树结构（包含子分类）。')
@category_bp.output(CategoryTreeSchema(many=True))
def get_category_tree():
    """Get full category tree structure"""
    # Optimized: Fetch all and build tree in memory or use CTE if needed.
    # For simplicity, we fetch roots and let Marshmallow recurse (N+1 risk, but ok for small trees)
    roots = db.session.scalars(select(Category).where(Category.parent_id.is_(None))).all()
    # BaseResponse wrapper applied automatically
    return {'data': roots}

@category_bp.post('')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='创建分类', description='创建一个新分类。')
@category_bp.input(CategoryBaseSchema, arg_name='data') # Fix: Explicit arg_name
@category_bp.output(CategoryDetailSchema)
def create_category(data):
    """Create a new category"""
    cat = Category(**data)
    db.session.add(cat)
    db.session.commit()
    return {'data': cat}

@category_bp.get('/<int:category_id>/attributes')
@category_bp.auth_required(auth)
@category_bp.doc(
    summary='获取分类属性', 
    description='获取指定分类的所有可用属性定义（包括从父分类继承的属性）。'
)
@category_bp.output(AttributeDefinitionSchema(many=True))
def get_category_attributes(category_id):
    """Get all available attributes for a category (including inherited)"""
    # TODO: Implement inheritance logic (walk up the tree)
    # Current implementation: Only direct attributes
    attributes = db.session.scalars(
        select(AttributeDefinition)
        .join(CategoryAttribute)
        .where(CategoryAttribute.category_id == category_id)
        .order_by(CategoryAttribute.display_order)
    ).all()
    return {'data': attributes}
