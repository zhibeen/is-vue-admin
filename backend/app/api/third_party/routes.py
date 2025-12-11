from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.extensions import db
from app.models.warehouse import WarehouseThirdPartyService, Warehouse, WarehouseThirdPartyWarehouse
from app.schemas.warehouse.third_party import ThirdPartyServiceSchema, ThirdPartyWarehouseSchema
from app.security import auth
from app.decorators import permission_required
from sqlalchemy import select
from datetime import datetime

third_party_bp = APIBlueprint('third_party', __name__, url_prefix='/third-party', tag='三方服务商')

class ThirdPartyServiceListAPI(MethodView):
    decorators = [third_party_bp.auth_required(auth)]
    
    @third_party_bp.output(ThirdPartyServiceSchema(many=True))
    def get(self):
        """获取三方服务商列表"""
        services = db.session.execute(select(WarehouseThirdPartyService)).scalars().all()
        return {'data': services}

class ThirdPartyWarehouseListAPI(MethodView):
    decorators = [third_party_bp.auth_required(auth)]
    
    @third_party_bp.output(ThirdPartyWarehouseSchema(many=True))
    def get(self, service_id):
        """获取指定服务商下的已同步仓库列表 (从本地数据库)"""
        # 1. 检查服务商是否存在
        service = db.session.get(WarehouseThirdPartyService, service_id)
        if not service:
            return {'data': []}
            
        # 2. 查询本地表
        warehouses = db.session.execute(
            select(WarehouseThirdPartyWarehouse).where(WarehouseThirdPartyWarehouse.service_id == service_id)
        ).scalars().all()
        
        # 3. 检查绑定状态
        # 查询当前系统中所有已绑定该服务商的仓库
        bound_warehouses = db.session.execute(
            select(Warehouse).where(Warehouse.third_party_service_id == service_id)
        ).scalars().all()
        
        # 建立映射: third_party_warehouse_id -> Warehouse Name
        bound_map = {}
        for w in bound_warehouses:
            if w.third_party_warehouse_id:
                bound_map[w.third_party_warehouse_id] = w.name
                
        # 4. 组装结果
        result = []
        for w in warehouses:
            # 转换为字典以便添加额外字段
            item = {
                'id': w.id,
                'code': w.code,
                'name': w.name,
                'country_code': w.country_code,
                'is_active': w.is_active,
                'note': w.note,
                'last_synced_at': w.last_synced_at.isoformat() if w.last_synced_at else None,
                'is_bound': w.id in bound_map,
                'bound_warehouse_name': bound_map.get(w.id)
            }
            result.append(item)
            
        return {'data': result}

class ThirdPartyWarehouseSyncAPI(MethodView):
    decorators = [third_party_bp.auth_required(auth)]
    
    @third_party_bp.doc(summary='手动触发全量同步', description='从三方API拉取最新仓库列表并更新本地表')
    def post(self, service_id):
        """手动触发全量同步"""
        service = db.session.get(WarehouseThirdPartyService, service_id)
        if not service:
            return {'message': '服务商不存在'}, 404
            
        # TODO: 这里应该调用 Adapter 模式的 Service
        # 目前先用 Mock 数据模拟全量拉取过程
        mock_data = []
        if service.code == 'goodcang':
            mock_data = [
                {'code': 'GC-US-EAST', 'name': '谷仓美东仓', 'country': 'US'},
                {'code': 'GC-US-WEST', 'name': '谷仓美西仓', 'country': 'US'},
                {'code': 'GC-DE', 'name': '谷仓德国仓', 'country': 'DE'},
                {'code': 'GC-JP', 'name': '谷仓日本仓', 'country': 'JP'}, # 新增一个
            ]
        elif service.code == 'winit':
            mock_data = [
                {'code': 'WI-US-01', 'name': '万邑通美西1仓', 'country': 'US'},
                {'code': 'WI-UK-01', 'name': '万邑通英国1仓', 'country': 'GB'},
            ]
            
        # 执行 Upsert (存在更新，不存在插入)
        synced_count = 0
        for item in mock_data:
            stmt = select(WarehouseThirdPartyWarehouse).where(
                WarehouseThirdPartyWarehouse.service_id == service_id,
                WarehouseThirdPartyWarehouse.code == item['code']
            )
            existing = db.session.execute(stmt).scalar_one_or_none()
            
            if existing:
                existing.name = item['name']
                existing.country_code = item['country']
                existing.last_synced_at = datetime.utcnow()
            else:
                new_wh = WarehouseThirdPartyWarehouse(
                    service_id=service_id,
                    code=item['code'],
                    name=item['name'],
                    country_code=item['country'],
                    is_active=False, # 默认为禁用，需手动开启
                    last_synced_at=datetime.utcnow()
                )
                db.session.add(new_wh)
            synced_count += 1
            
        db.session.commit()
        return {'message': '同步成功', 'data': {'synced_count': synced_count}}

third_party_bp.add_url_rule('/services', view_func=ThirdPartyServiceListAPI.as_view('service_list'))
third_party_bp.add_url_rule('/services/<int:service_id>/warehouses', view_func=ThirdPartyWarehouseListAPI.as_view('warehouse_list'))
third_party_bp.add_url_rule('/services/<int:service_id>/sync-warehouses', view_func=ThirdPartyWarehouseSyncAPI.as_view('warehouse_sync'))
