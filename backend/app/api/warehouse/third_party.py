from apiflask import APIBlueprint, Schema
from apiflask.fields import String, Integer, Boolean, DateTime, List, Nested, Float, Dict
from apiflask.views import MethodView
from app.extensions import db
from app.models.warehouse.third_party import WarehouseThirdPartyService, WarehouseThirdPartyWarehouse, WarehouseThirdPartyWarehouseMap, WarehouseThirdPartySkuMapping, WarehouseThirdPartyProduct
from app.models.warehouse.warehouse import Warehouse
from app.security import auth
from app.decorators import permission_required
from flask import request
import datetime
import json
from sqlalchemy.orm import joinedload

third_party_bp = APIBlueprint('third_party', __name__, url_prefix='/third-party', tag='三方服务管理')

# --- Schemas ---

class ThirdPartyServiceSchema(Schema):
    id = Integer(dump_only=True)
    name = String(required=True)
    code = String(required=True)
    provider_code = String(required=True)
    app_key = String()
    # app_secret 不返回
    is_active = Boolean()
    status = String()
    last_sync_time = DateTime()
    api_url = String()

class ServiceCreateSchema(Schema):
    name = String(required=True)
    code = String(required=True) # 别名
    provider_code = String(required=True) # 4px, winit
    api_url = String(load_default='')
    app_key = String()
    app_secret = String()
    is_active = Boolean(load_default=True)

class ServiceUpdateSchema(Schema):
    name = String()
    api_url = String()
    app_key = String()
    app_secret = String()
    is_active = Boolean()

class TestConnectionSchema(Schema):
    provider_code = String(required=True)
    api_url = String(required=True)
    app_key = String(required=True)
    app_secret = String(required=True)

class TestConnectionResultSchema(Schema):
    success = Boolean()
    message = String()

class RemoteWarehouseSchema(Schema):
    remote_code = String()
    remote_name = String()
    is_bound = Boolean()
    local_warehouse_id = Integer(allow_none=True)
    local_warehouse_name = String(allow_none=True)

class BindWarehouseSchema(Schema):
    remote_code = String(required=True)
    remote_name = String(required=True)
    action = String(required=True) # create_new, bind_existing
    local_id = Integer(load_default=None)

# (v1.6) New Schemas for Detail Page
class WarehouseThirdPartyWarehouseSchema(Schema):
    id = Integer(dump_only=True)
    code = String()
    name = String()
    country_code = String()
    is_active = Boolean() # 是否启用(关联本地)
    note = String()
    last_synced_at = DateTime()
    
    # 关联的本地仓库信息(如有)
    service_warehouse_name = String(dump_only=True) # 方便前端显示

class ToggleWarehouseInput(Schema):
    is_active = Boolean(required=True)

# (v1.7) SKU Mapping Schemas
class SkuMappingSchema(Schema):
    id = Integer(dump_only=True)
    service_id = Integer()
    warehouse_id = Integer(allow_none=True) # None = Level 2 (Global)
    
    remote_sku = String(required=True)
    local_sku = String(required=True)
    quantity_ratio = Float(load_default=1.0)
    
    # 辅助字段 (Frontend display)
    warehouse_name = String(dump_only=True)
    is_global = Boolean(dump_only=True)
    
    # (v1.9) Product details from JOIN
    product_image = String(dump_only=True)
    product_specs = Dict(dump_only=True)

class SkuMappingQuerySchema(Schema):
    warehouse_id = Integer(load_default=None) # Filter by specific warehouse
    status = String(load_default='all') # all, mapped, unmapped
    q = String() # Search keyword

class SkuMappingInput(Schema):
    warehouse_id = Integer(allow_none=True)
    remote_sku = String(required=True)
    local_sku = String(required=True)
    quantity_ratio = Float(load_default=1.0)

# (v1.8) Third Party Product Schemas
class ThirdPartyProductSchema(Schema):
    id = Integer(dump_only=True)
    remote_sku = String()
    remote_name = String()
    specs = Dict(dump_default={})
    image_url = String(allow_none=True)
    last_synced_at = DateTime()

class SyncProductsResultSchema(Schema):
    synced_count = Integer()
    message = String()

# --- Routes ---

class ServiceListAPI(MethodView):
    decorators = [third_party_bp.auth_required(auth)]
    
    @third_party_bp.output(ThirdPartyServiceSchema(many=True))
    def get(self):
        """获取服务商列表"""
        services = db.session.query(WarehouseThirdPartyService).all()
        return {'data': services}
    
    @third_party_bp.input(ServiceCreateSchema, arg_name='data')
    @third_party_bp.output(ThirdPartyServiceSchema)
    def post(self, data):
        """创建服务商"""
        service = WarehouseThirdPartyService(**data)
        db.session.add(service)
        db.session.commit()
        return {'data': service}

class ServiceItemAPI(MethodView):
    decorators = [third_party_bp.auth_required(auth)]
    
    @third_party_bp.output(ThirdPartyServiceSchema)
    def get(self, service_id):
        service = db.session.get(WarehouseThirdPartyService, service_id)
        return {'data': service}
    
    @third_party_bp.input(ServiceUpdateSchema, arg_name='data')
    @third_party_bp.output(ThirdPartyServiceSchema)
    def put(self, service_id, data):
        """更新服务商"""
        service = db.session.get(WarehouseThirdPartyService, service_id)
        if not service:
            return {'message': 'Service not found'}, 404
        
        for key, value in data.items():
            if value is not None:
                setattr(service, key, value)
        
        db.session.commit()
        return {'data': service}
    
    def delete(self, service_id):
        service = db.session.get(WarehouseThirdPartyService, service_id)
        if service:
            db.session.delete(service)
            db.session.commit()
        return {'data': None}

class TestConnectionAPI(MethodView):
    decorators = [third_party_bp.auth_required(auth)]
    
    @third_party_bp.input(TestConnectionSchema, arg_name='data')
    @third_party_bp.output(TestConnectionResultSchema)
    def post(self, data):
        """测试API连接"""
        try:
            # 根据不同的服务商调用不同的测试接口
            provider_code = data['provider_code']
            api_url = data['api_url']
            app_key = data['app_key']
            app_secret = data['app_secret']
            
            # 如果密码为空，尝试从数据库查找对应的服务商
            if not app_secret and app_key:
                # 查找是否有相同配置的服务商
                service = db.session.query(WarehouseThirdPartyService).filter_by(
                    provider_code=provider_code,
                    api_url=api_url,
                    app_key=app_key
                ).first()
                
                if service and service.app_secret:
                    app_secret = service.app_secret
                else:
                    return {'data': {'success': False, 'message': '未找到有效的密码配置'}}
            
            # 模拟测试连接
            # 实际开发中这里应该调用真实的API进行测试
            if provider_code == '4px':
                # 模拟成功响应
                return {'data': {'success': True, 'message': '连接成功'}}
            elif provider_code == 'winit':
                # 模拟成功响应
                return {'data': {'success': True, 'message': '连接成功'}}
            else:
                # 模拟成功响应
                return {'data': {'success': True, 'message': '连接成功'}}
                
        except Exception as e:
            return {'data': {'success': False, 'message': f'连接失败: {str(e)}'}}

class SyncWarehousesAPI(MethodView):
    decorators = [third_party_bp.auth_required(auth)]
    
    @third_party_bp.output(RemoteWarehouseSchema(many=True))
    def post(self, service_id):
        """同步远程仓库列表 (Mock) - 兼容旧接口"""
        service = db.session.get(WarehouseThirdPartyService, service_id)
        if not service:
            return {'message': 'Service not found'}, 404
            
        # 这里为了兼容旧接口逻辑，暂时返回一个空列表或模拟数据
        # 实际逻辑应该是触发全量同步任务(Celery)，然后前端轮询
        # 现在我们假设同步是同步进行的 (用于演示)
        
        # 1. 模拟从API获取数据
        # ... (略)
        
        # 2. 更新到 WarehouseThirdPartyWarehouse 表 (新表)
        # 本次简化：直接返回成功
        
        service.last_sync_time = datetime.datetime.utcnow()
        service.status = 'connected'
        db.session.commit()
        
        return {'data': []}

class WarehouseListAPI(MethodView):
    """(v1.6) 获取服务商下的子仓库列表"""
    decorators = [third_party_bp.auth_required(auth)]

    @third_party_bp.output(WarehouseThirdPartyWarehouseSchema(many=True))
    def get(self, service_id):
        # 预加载关联的本地仓库信息
        warehouses = db.session.query(WarehouseThirdPartyWarehouse)\
            .options(joinedload(WarehouseThirdPartyWarehouse.bound_local_warehouses))\
            .filter_by(service_id=service_id).all()
        
        results = []
        for w in warehouses:
            # 查找关联的本地仓库名称
            # 注意：Warehouse.third_party_warehouse_id 指向 w.id
            # 但这里是一对多关系? 一个 TPW 只能对应一个 LocalW (理论上)
            local_wh = w.bound_local_warehouses[0] if w.bound_local_warehouses else None
            
            results.append({
                'id': w.id,
                'code': w.code,
                'name': w.name,
                'country_code': w.country_code,
                'is_active': w.is_active,
                'note': w.note,
                'last_synced_at': w.last_synced_at,
                'service_warehouse_name': local_wh.name if local_wh else None
            })
            
        return {'data': results}

class WarehouseToggleAPI(MethodView):
    """(v1.6) 切换仓库启用状态"""
    decorators = [third_party_bp.auth_required(auth)]

    @third_party_bp.input(ToggleWarehouseInput)
    def put(self, service_id, warehouse_id, data):
        tp_wh = db.session.get(WarehouseThirdPartyWarehouse, warehouse_id)
        if not tp_wh:
            return {'message': 'Third party warehouse not found'}, 404
            
        if tp_wh.service_id != service_id:
            return {'message': 'Service mismatch'}, 400
            
        target_status = data['is_active']
        
        if target_status == tp_wh.is_active:
            return {'message': 'Status unchanged'}, 200
            
        # 切换逻辑
        tp_wh.is_active = target_status
        
        # 查找是否已存在本地仓库关联
        local_wh = db.session.query(Warehouse).filter_by(third_party_warehouse_id=tp_wh.id).first()
        
        if target_status: # 启用
            if not local_wh:
                # 自动创建本地仓库
                service = db.session.get(WarehouseThirdPartyService, service_id)
                new_wh = Warehouse(
                    code=tp_wh.code, # 如果冲突可能需要加前缀
                    name=f"{service.name} {tp_wh.code}", # 默认命名规则
                    category='physical',
                    location_type='overseas', # 假设全是海外仓
                    ownership_type='third_party',
                    third_party_service_id=service_id,
                    third_party_warehouse_id=tp_wh.id,
                    status='active'
                )
                db.session.add(new_wh)
            else:
                # 激活现有仓库
                local_wh.status = 'active'
        else: # 禁用
            if local_wh:
                # 标记为废弃或隐藏? 或者仅改变状态
                local_wh.status = 'deprecated' 
        
        db.session.commit()
        return {'message': 'Status updated'}

class SkuMappingListAPI(MethodView):
    """(v1.7) SKU 映射管理"""
    decorators = [third_party_bp.auth_required(auth)]

    @third_party_bp.input(SkuMappingQuerySchema, location='query')
    @third_party_bp.output(SkuMappingSchema(many=True))
    def get(self, service_id, query_data):
        # 基础查询 (Left Outer Join Product to get details)
        q = db.session.query(WarehouseThirdPartySkuMapping, WarehouseThirdPartyProduct)\
            .outerjoin(WarehouseThirdPartyProduct, db.and_(
                WarehouseThirdPartySkuMapping.service_id == WarehouseThirdPartyProduct.service_id,
                WarehouseThirdPartySkuMapping.remote_sku == WarehouseThirdPartyProduct.remote_sku
            ))\
            .filter(WarehouseThirdPartySkuMapping.service_id == service_id)
        
        # 筛选仓库
        if query_data['warehouse_id']:
            q = q.filter(WarehouseThirdPartySkuMapping.warehouse_id == query_data['warehouse_id'])
        
        # 搜索 (支持搜本地SKU或远程SKU)
        if query_data.get('q'):
            keyword = f"%{query_data['q']}%"
            q = q.filter(db.or_(
                WarehouseThirdPartySkuMapping.remote_sku.ilike(keyword),
                WarehouseThirdPartySkuMapping.local_sku.ilike(keyword)
            ))

        # q.all() returns list of tuples (mapping, product)
        results_data = q.all()
        
        # 转换数据以适配 Schema
        results = []
        for m, p in results_data:
            results.append({
                'id': m.id,
                'service_id': m.service_id,
                'warehouse_id': m.warehouse_id,
                'remote_sku': m.remote_sku,
                'local_sku': m.local_sku,
                'quantity_ratio': m.quantity_ratio,
                'is_global': m.warehouse_id is None,
                'warehouse_name': m.warehouse.name if m.warehouse_id else '全部仓库(通用)',
                # Product details if joined
                'product_image': p.image_url if p else None,
                'product_specs': p.specs if p else {}
            })
            
        return {'data': results}

    @third_party_bp.input(SkuMappingInput)
    def post(self, service_id, data):
        """创建/更新映射"""
        
        # (v1.9) Validation Warning: Check if product exists
        product_exists = db.session.query(WarehouseThirdPartyProduct).filter_by(
            service_id=service_id, 
            remote_sku=data['remote_sku']
        ).first()
        
        # 查找是否存在 (Level 2 or Level 3 match)
        mapping = db.session.query(WarehouseThirdPartySkuMapping).filter_by(
            service_id=service_id,
            warehouse_id=data['warehouse_id'],
            remote_sku=data['remote_sku']
        ).first()
        
        if not mapping:
            mapping = WarehouseThirdPartySkuMapping(
                service_id=service_id,
                warehouse_id=data['warehouse_id'],
                remote_sku=data['remote_sku']
            )
            db.session.add(mapping)
            
        mapping.local_sku = data['local_sku']
        mapping.quantity_ratio = data['quantity_ratio']
        
        db.session.commit()
        
        response = {'data': {'id': mapping.id}, 'message': 'Mapping saved'}
        if not product_exists:
            response['warning'] = f"Warning: Remote SKU '{data['remote_sku']}' not found in product list. Please sync products."
            
        return response

class SkuMappingItemAPI(MethodView):
    decorators = [third_party_bp.auth_required(auth)]

    def delete(self, service_id, mapping_id):
        mapping = db.session.get(WarehouseThirdPartySkuMapping, mapping_id)
        if mapping and mapping.service_id == service_id:
            db.session.delete(mapping)
            db.session.commit()
        return {'message': 'Deleted'}

class SyncProductsAPI(MethodView):
    """(v1.8) 同步三方商品"""
    decorators = [third_party_bp.auth_required(auth)]

    @third_party_bp.output(SyncProductsResultSchema)
    def post(self, service_id):
        service = db.session.get(WarehouseThirdPartyService, service_id)
        if not service:
            return {'message': 'Service not found'}, 404
            
        # 模拟同步逻辑 (Mock data)
        # 实际应调用第三方API获取商品列表
        mock_products = []
        for i in range(1, 21):
            mock_products.append({
                'remote_sku': f'MOCK-PROD-{i:03d}',
                'remote_name': f'Mock Product {i} (Synced)',
                'specs': {'weight': 1.5, 'dim': [10, 10, 10]}
            })
            
        synced_count = 0
        for p in mock_products:
            # 查找是否存在
            product = db.session.query(WarehouseThirdPartyProduct).filter_by(
                service_id=service_id,
                remote_sku=p['remote_sku']
            ).first()
            
            if not product:
                product = WarehouseThirdPartyProduct(
                    service_id=service_id,
                    remote_sku=p['remote_sku'],
                    remote_name=p['remote_name'],
                    specs=p['specs']
                )
                db.session.add(product)
                synced_count += 1
            else:
                # 更新信息
                product.remote_name = p['remote_name']
                product.specs = p['specs']
                product.last_synced_at = datetime.datetime.utcnow()
                
        db.session.commit()
        return {'data': {'synced_count': synced_count, 'message': 'Sync completed'}}

class ThirdPartyProductListAPI(MethodView):
    """(v1.8) 获取三方商品列表 (用于下拉选择)"""
    decorators = [third_party_bp.auth_required(auth)]
    
    @third_party_bp.output(ThirdPartyProductSchema(many=True))
    def get(self, service_id):
        products = db.session.query(WarehouseThirdPartyProduct).filter_by(service_id=service_id).all()
        return {'data': products}

# Register Routes
third_party_bp.add_url_rule('/services', view_func=ServiceListAPI.as_view('service_list'))
third_party_bp.add_url_rule('/services/<int:service_id>', view_func=ServiceItemAPI.as_view('service_item'))
third_party_bp.add_url_rule('/test-connection', view_func=TestConnectionAPI.as_view('test_connection'))
third_party_bp.add_url_rule('/services/<int:service_id>/sync-warehouses', view_func=SyncWarehousesAPI.as_view('sync_warehouses'))
# New Routes
third_party_bp.add_url_rule('/services/<int:service_id>/warehouses', view_func=WarehouseListAPI.as_view('warehouse_list'))
third_party_bp.add_url_rule('/services/<int:service_id>/warehouses/<int:warehouse_id>/toggle', view_func=WarehouseToggleAPI.as_view('warehouse_toggle'))
third_party_bp.add_url_rule('/services/<int:service_id>/sku-mappings', view_func=SkuMappingListAPI.as_view('sku_mappings_list'))
third_party_bp.add_url_rule('/services/<int:service_id>/sku-mappings/<int:mapping_id>', view_func=SkuMappingItemAPI.as_view('sku_mappings_item'))
third_party_bp.add_url_rule('/services/<int:service_id>/products/sync', view_func=SyncProductsAPI.as_view('sync_products'))
third_party_bp.add_url_rule('/services/<int:service_id>/products', view_func=ThirdPartyProductListAPI.as_view('third_party_products'))
