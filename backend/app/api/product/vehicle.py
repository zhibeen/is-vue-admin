from apiflask import APIBlueprint, abort
from sqlalchemy import select
from app.extensions import db
from app.models.vehicle import VehicleAux
from app.schemas.vehicle import (
    BrandCreateSchema, BrandUpdateSchema, BrandOutSchema,
    ModelCreateSchema, ModelOutSchema,
    SubmodelCreateSchema, SubmodelOutSchema,
    VehicleAuxBaseSchema
)
from app.security import auth

from app.decorators import permission_required

# url_prefix is now /vehiclesaux (relative to api_v1)
vehicle_bp = APIBlueprint('vehicle_aux', __name__, url_prefix='/vehiclesaux', tag='VehicleAux')

# --- Brands ---

@vehicle_bp.get('/brands')
@vehicle_bp.auth_required(auth)
@vehicle_bp.doc(summary='获取品牌列表', description='获取所有车辆品牌，按代码排序。')
@vehicle_bp.output(BrandOutSchema(many=True))
def get_brands():
    """List all brands"""
    brands = db.session.scalars(
        select(VehicleAux).filter_by(level_type='brand').order_by(VehicleAux.code)
    ).all()
    # Auto-wrapped by BaseResponse
    return {'data': brands}

@vehicle_bp.post('/brands')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(summary='创建品牌', description='创建一个新的车辆品牌。需要提供名称、代码和缩写。')
@vehicle_bp.input(BrandCreateSchema)
@vehicle_bp.output(BrandOutSchema, status_code=201)
def create_brand(data):
    """Create a brand"""
    brand = VehicleAux(
        name=data['name'],
        code=data['code'],
        abbr=data['abbr'],
        level_type='brand'
    )
    db.session.add(brand)
    db.session.commit()
    return {'data': brand}

@vehicle_bp.put('/brands/<int:brand_id>')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(
    summary='更新品牌', 
    description='更新指定品牌的名称、代码或缩写。'
)
@vehicle_bp.input(BrandUpdateSchema)
@vehicle_bp.output(BrandOutSchema)
def update_brand(brand_id, data):
    """Update a brand"""
    brand = db.session.get(VehicleAux, brand_id)
    if not brand or brand.level_type != 'brand':
        abort(404)
    
    for key, value in data.items():
        setattr(brand, key, value)
        
    db.session.commit()
    return {'data': brand}

@vehicle_bp.delete('/brands/<int:brand_id>')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(
    summary='删除品牌', 
    description='删除指定品牌。如果该品牌下有车型，可能会失败（取决于数据库约束）。'
)
def delete_brand(brand_id):
    """Delete a brand"""
    brand = db.session.get(VehicleAux, brand_id)
    if not brand or brand.level_type != 'brand':
        abort(404)
    
    # Check if children exist (optional, usually database constraints or cascade)
    # But for safety, we can check
    # children = db.session.scalars(select(VehicleAux).filter_by(parent_id=brand_id)).first()
    # if children:
    #    abort(400, 'Cannot delete brand with models')
        
    db.session.delete(brand)
    db.session.commit()
    return {'code': 0, 'message': 'success', 'data': None}

# --- Models ---

@vehicle_bp.get('/brands/<int:brand_id>/models')
@vehicle_bp.auth_required(auth)
@vehicle_bp.doc(
    summary='获取品牌车型列表', 
    description='获取指定品牌下的所有车型。'
)
@vehicle_bp.output(ModelOutSchema(many=True))
def get_models(brand_id):
    """List models for a brand"""
    brand = db.session.get(VehicleAux, brand_id)
    if not brand or brand.level_type != 'brand':
        abort(404, 'Brand not found')
        
    models = db.session.scalars(
        select(VehicleAux).filter_by(parent_id=brand_id, level_type='model').order_by(VehicleAux.name)
    ).all()
    return {'data': models}

@vehicle_bp.post('/models')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(summary='创建车型', description='为指定品牌创建一个新车型。')
@vehicle_bp.input(ModelCreateSchema)
@vehicle_bp.output(ModelOutSchema, status_code=201)
def create_model(data):
    """Create a model"""
    brand = db.session.get(VehicleAux, data['brand_id'])
    if not brand or brand.level_type != 'brand':
        abort(404, 'Brand not found')

    model = VehicleAux(
        name=data['name'],
        parent_id=data['brand_id'],
        level_type='model'
    )
    db.session.add(model)
    db.session.commit()
    return {'data': model}

@vehicle_bp.put('/models/<int:model_id>')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(
    summary='更新车型', 
    description='更新指定车型的名称。'
)
@vehicle_bp.input(VehicleAuxBaseSchema)
@vehicle_bp.output(ModelOutSchema)
def update_model(model_id, data):
    """Update a model"""
    model = db.session.get(VehicleAux, model_id)
    if not model or model.level_type != 'model':
        abort(404)
        
    model.name = data['name']
    db.session.commit()
    return {'data': model}

@vehicle_bp.delete('/models/<int:model_id>')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(
    summary='删除车型', 
    description='删除指定车型。'
)
def delete_model(model_id):
    """Delete a model"""
    model = db.session.get(VehicleAux, model_id)
    if not model or model.level_type != 'model':
        abort(404)
        
    db.session.delete(model)
    db.session.commit()
    return {'code': 0, 'message': 'success', 'data': None}

# --- Submodels ---

@vehicle_bp.get('/models/<int:model_id>/submodels')
@vehicle_bp.auth_required(auth)
@vehicle_bp.doc(
    summary='获取车型子型号列表', 
    description='获取指定车型下的所有子型号（如具体排量、年份配置）。'
)
@vehicle_bp.output(SubmodelOutSchema(many=True))
def get_submodels(model_id):
    """List submodels for a model"""
    model = db.session.get(VehicleAux, model_id)
    if not model or model.level_type != 'model':
        abort(404, 'Model not found')
        
    submodels = db.session.scalars(
        select(VehicleAux).filter_by(parent_id=model_id, level_type='submodel').order_by(VehicleAux.name)
    ).all()
    return {'data': submodels}

@vehicle_bp.post('/submodels')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(summary='创建子型号', description='为指定车型创建一个新子型号。')
@vehicle_bp.input(SubmodelCreateSchema)
@vehicle_bp.output(SubmodelOutSchema, status_code=201)
def create_submodel(data):
    """Create a submodel"""
    model = db.session.get(VehicleAux, data['model_id'])
    if not model or model.level_type != 'model':
        abort(404, 'Model not found')

    submodel = VehicleAux(
        name=data['name'],
        parent_id=data['model_id'],
        level_type='submodel'
    )
    db.session.add(submodel)
    db.session.commit()
    return {'data': submodel}

@vehicle_bp.put('/submodels/<int:submodel_id>')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(
    summary='更新子型号', 
    description='更新指定子型号的名称。'
)
@vehicle_bp.input(VehicleAuxBaseSchema)
@vehicle_bp.output(SubmodelOutSchema)
def update_submodel(submodel_id, data):
    """Update a submodel"""
    submodel = db.session.get(VehicleAux, submodel_id)
    if not submodel or submodel.level_type != 'submodel':
        abort(404)
        
    submodel.name = data['name']
    db.session.commit()
    return {'data': submodel}

@vehicle_bp.delete('/submodels/<int:submodel_id>')
@vehicle_bp.auth_required(auth)
@permission_required('vehicle:manage')
@vehicle_bp.doc(
    summary='删除子型号', 
    description='删除指定子型号。'
)
def delete_submodel(submodel_id):
    """Delete a submodel"""
    submodel = db.session.get(VehicleAux, submodel_id)
    if not submodel or submodel.level_type != 'submodel':
        abort(404)
        
    db.session.delete(submodel)
    db.session.commit()
    return {'code': 0, 'message': 'success', 'data': None}
