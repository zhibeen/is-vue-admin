from apiflask import APIBlueprint, abort
from sqlalchemy import select
from app.extensions import db
from app.models.product import ProductVehicle
from app.schemas.product.vehicle import ProductVehicleBaseSchema, ProductVehicleTreeSchema
from app.security import auth
from app.decorators import permission_required

# url_prefix is now /vehicles (relative to api_v1)
vehicle_bp = APIBlueprint('vehicle', __name__, url_prefix='/vehicles', tag='Vehicles')

@vehicle_bp.get('/tree')
@vehicle_bp.auth_required(auth)
@vehicle_bp.doc(summary='获取车辆层级树', description='获取完整的车辆层级树 (Brand -> Model -> Year)。')
@vehicle_bp.output(ProductVehicleTreeSchema(many=True))
def get_vehicle_tree():
    """Get full vehicle tree structure"""
    # Fetch roots (brands)
    roots = db.session.scalars(
        select(ProductVehicle)
        .where(ProductVehicle.parent_id.is_(None))
        .order_by(ProductVehicle.sort_order, ProductVehicle.name)
    ).all()
    return {'data': roots}

# --- Lazy Loading Endpoints ---

@vehicle_bp.get('/brands')
@vehicle_bp.auth_required(auth)
@vehicle_bp.doc(summary='获取所有品牌', description='获取第一级车辆品牌列表。')
@vehicle_bp.output(ProductVehicleBaseSchema(many=True))
def get_vehicle_brands():
    """Get vehicle brands (Level 1)"""
    brands = db.session.scalars(
        select(ProductVehicle)
        .where(ProductVehicle.level_type == 'make') # or parent_id is None
        .order_by(ProductVehicle.sort_order, ProductVehicle.name)
    ).all()
    return {'data': brands}

@vehicle_bp.get('/brands/<int:brand_id>/models')
@vehicle_bp.auth_required(auth)
@vehicle_bp.doc(summary='获取品牌下的车型', description='获取指定品牌下的车型列表。')
@vehicle_bp.output(ProductVehicleBaseSchema(many=True))
def get_vehicle_models(brand_id):
    """Get vehicle models (Level 2)"""
    models = db.session.scalars(
        select(ProductVehicle)
        .where(ProductVehicle.parent_id == brand_id)
        .order_by(ProductVehicle.sort_order, ProductVehicle.name)
    ).all()
    return {'data': models}

@vehicle_bp.get('/models/<int:model_id>/years')
@vehicle_bp.auth_required(auth)
@vehicle_bp.doc(summary='获取车型下的年份', description='获取指定车型下的年份列表。')
@vehicle_bp.output(ProductVehicleBaseSchema(many=True))
def get_vehicle_years(model_id):
    """Get vehicle years (Level 3)"""
    years = db.session.scalars(
        select(ProductVehicle)
        .where(ProductVehicle.parent_id == model_id)
        .order_by(ProductVehicle.sort_order, ProductVehicle.name)
    ).all()
    return {'data': years}

@vehicle_bp.post('')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(summary='创建车辆节点', description='创建 Brand, Model 或 Year 节点。')
@vehicle_bp.input(ProductVehicleBaseSchema, arg_name='data')
@vehicle_bp.output(ProductVehicleBaseSchema, status_code=201)
def create_vehicle_node(data):
    """Create a new vehicle node"""
    # Check uniqueness of abbreviation within the same level/parent
    stmt = select(ProductVehicle).where(
        ProductVehicle.abbreviation == data['abbreviation'],
        ProductVehicle.parent_id == data.get('parent_id')
    )
    if db.session.scalars(stmt).first():
        abort(400, 'Abbreviation already exists in this level')

    node = ProductVehicle(**data)
    db.session.add(node)
    db.session.commit()
    return {'data': node}

@vehicle_bp.delete('/<int:node_id>')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(summary='删除节点', description='删除指定节点。如果有子节点则无法删除。')
def delete_vehicle_node(node_id):
    """Delete a vehicle node"""
    node = db.session.get(ProductVehicle, node_id)
    if not node:
        abort(404)
    
    # Check children
    if node.children:
        abort(400, 'Cannot delete node with children')
        
    db.session.delete(node)
    db.session.commit()
    return {'code': 0, 'message': 'success', 'data': None}
