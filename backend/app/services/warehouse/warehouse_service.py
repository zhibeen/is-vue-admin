from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_, case
from sqlalchemy.orm import selectinload, joinedload
from app.extensions import db
from app.models.warehouse import Warehouse, WarehouseLocation
from app.errors import BusinessError
import logging

logger = logging.getLogger(__name__)


class WarehouseService:
    """仓库服务"""
    
    def __init__(self):
        pass
    
    def get_stats(self) -> Dict[str, int]:
        """获取仓库统计信息"""
        stats = {
            'total': 0,
            'physical': 0,
            'virtual': 0,
            'domestic': 0,
            'overseas': 0,
            'active': 0
        }
        
        # 使用 case when 统计各项数据
        stmt = select(
            db.func.count(Warehouse.id).label('total'),
            db.func.sum(case((Warehouse.category == 'physical', 1), else_=0)).label('physical'),
            db.func.sum(case((Warehouse.category == 'virtual', 1), else_=0)).label('virtual'),
            db.func.sum(case((Warehouse.location_type == 'domestic', 1), else_=0)).label('domestic'),
            db.func.sum(case((Warehouse.location_type == 'overseas', 1), else_=0)).label('overseas'),
            db.func.sum(case((Warehouse.status == 'active', 1), else_=0)).label('active'),
        )
        
        result = db.session.execute(stmt).one()
        
        stats['total'] = result.total or 0
        stats['physical'] = result.physical or 0
        stats['virtual'] = result.virtual or 0
        stats['domestic'] = result.domestic or 0
        stats['overseas'] = result.overseas or 0
        stats['active'] = result.active or 0
        
        return stats
    
    def get_list(self, page: int = 1, per_page: int = 20, keyword: Optional[str] = None, 
                 category: Optional[str] = None, location_type: Optional[str] = None,
                 ownership_type: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """获取仓库列表"""
        # DEBUG: 打印详细参数，排查请求逻辑
        logger.info('DEBUG: get_list args', extra={
            'raw_category': category,
            'raw_category_type': type(category).__name__,
            'raw_location': location_type
        })

        logger.info('获取仓库列表', extra={
            'page': page,
            'per_page': per_page,
            'keyword': keyword,
            'category': category,
            'location_type': location_type,
            'ownership_type': ownership_type,
            'status': status
        })
        
        query = select(Warehouse)
        
        # 搜索条件
        conditions = []
        
        if keyword:
            conditions.append(
                or_(
                    Warehouse.code.ilike(f'%{keyword}%'),
                    Warehouse.name.ilike(f'%{keyword}%')
                )
            )
        
        # 支持多值筛选：使用逗号分隔的字符串，如 "physical,virtual"
        if category:
            categories = [c.strip() for c in category.split(',') if c.strip()]
            logger.info(f'DEBUG: Parsed categories for filtering: {categories}')
            if len(categories) == 1:
                conditions.append(Warehouse.category == categories[0])
            elif len(categories) > 1:
                conditions.append(Warehouse.category.in_(categories))
        
        if location_type:
            location_types = [lt.strip() for lt in location_type.split(',') if lt.strip()]
            if len(location_types) == 1:
                conditions.append(Warehouse.location_type == location_types[0])
            elif len(location_types) > 1:
                conditions.append(Warehouse.location_type.in_(location_types))
        
        if ownership_type:
            ownership_types = [ot.strip() for ot in ownership_type.split(',') if ot.strip()]
            if len(ownership_types) == 1:
                conditions.append(Warehouse.ownership_type == ownership_types[0])
            elif len(ownership_types) > 1:
                conditions.append(Warehouse.ownership_type.in_(ownership_types))
        
        if status:
            statuses = [s.strip() for s in status.split(',') if s.strip()]
            if len(statuses) == 1:
                conditions.append(Warehouse.status == statuses[0])
            elif len(statuses) > 1:
                conditions.append(Warehouse.status.in_(statuses))
        
        # 应用所有条件，使用 OR 连接
        if conditions:
            query = query.where(or_(*conditions))
        
        # 分页
        total = db.session.execute(select(db.func.count()).select_from(query.subquery())).scalar()
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        # DEBUG: 打印生成的 SQL
        try:
            compiled_sql = str(query.compile(compile_kwargs={"literal_binds": True}))
            logger.info(f'DEBUG: Generated SQL: {compiled_sql}')
        except Exception as e:
            logger.warning(f'DEBUG: Could not compile SQL: {e}')

        # 执行查询
        warehouses = db.session.execute(query).scalars().all()
        
        logger.info('仓库列表查询完成', extra={
            'total': total,
            'returned_count': len(warehouses)
        })
        
        return {
            'items': warehouses,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    
    def get_warehouse(self, warehouse_id: int) -> Warehouse:
        """获取仓库详情"""
        warehouse = db.session.get(Warehouse, warehouse_id)
        if not warehouse:
            raise BusinessError(f'仓库 {warehouse_id} 不存在', code=404)
        return warehouse
    
    def _clean_data(self, data: Dict[str, Any], current_category: Optional[str] = None) -> Dict[str, Any]:
        """
        数据清洗：根据仓库形态清理互斥字段
        防呆设计：防止前端传来脏数据
        """
        # 优先使用 payload 中的 category，如果是 Update 且 payload 中无 category，则使用数据库中的 current_category
        category = data.get('category', current_category)
        
        if not category:
            return data
            
        # 场景 A: 实体仓 (physical) -> 必须清空子仓关联 (virtual only)
        if category == 'physical':
            # 显式将 child_warehouse_ids 设为 None (如果 payload 中包含该字段)
            if 'child_warehouse_ids' in data or current_category == 'virtual':
                # 如果从 virtual 变为 physical，或者 payload 包含此字段，强制清空
                data['child_warehouse_ids'] = None

        # 场景 B: 虚拟仓 (virtual) -> 必须清空物理属性 (physical only)
        if category == 'virtual':
            if 'capacity' in data or current_category == 'physical':
                data['capacity'] = None
            if 'max_volume' in data or current_category == 'physical':
                data['max_volume'] = None
                
        return data

    def create_warehouse(self, data: Dict[str, Any], user_id: Optional[int] = None) -> Warehouse:
        """创建仓库"""
        # 检查编码是否重复
        existing = db.session.execute(
            select(Warehouse).where(Warehouse.code == data['code'])
        ).scalar_one_or_none()
        
        if existing:
            raise BusinessError(f'仓库编码 {data["code"]} 已存在', code=400)
        
        # 防呆清洗
        data = self._clean_data(data)
        
        # 创建仓库
        warehouse = Warehouse(
            code=data['code'],
            name=data['name'],
            category=data.get('category', 'physical'),
            location_type=data.get('location_type', 'domestic'),
            ownership_type=data.get('ownership_type', 'self'),
            status=data.get('status', 'active'),
            business_type=data.get('business_type', 'standard'),
            currency=data.get('currency', 'USD'),
            api_config=data.get('api_config'),
            child_warehouse_ids=data.get('child_warehouse_ids'),
            capacity=data.get('capacity'),
            max_volume=data.get('max_volume'),
            timezone=data.get('timezone', 'UTC'),
            contact_person=data.get('contact_person'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email'),
            address=data.get('address'),
            created_by=user_id
        )
        
        db.session.add(warehouse)
        db.session.commit()
        
        logger.info('仓库创建成功', extra={
            'warehouse_id': warehouse.id,
            'code': warehouse.code,
            'created_by': user_id
        })
        
        return warehouse
    
    def update_warehouse(self, warehouse_id: int, data: Dict[str, Any]) -> Warehouse:
        """更新仓库"""
        warehouse = self.get_warehouse(warehouse_id)
        
        # 防呆清洗 (传入当前 category)
        data = self._clean_data(data, current_category=warehouse.category)
        
        # 更新字段
        for key, value in data.items():
            if hasattr(warehouse, key):
                 # 如果是 update 操作，允许 value 为 None (用于清空字段)
                 # 只要 key 存在于 data 中，就执行更新
                 setattr(warehouse, key, value)
        
        db.session.commit()
        
        logger.info('仓库更新成功', extra={
            'warehouse_id': warehouse_id,
            'updated_fields': list(data.keys())
        })
        
        return warehouse
    
    def delete_warehouse(self, warehouse_id: int) -> None:
        """删除仓库"""
        warehouse = self.get_warehouse(warehouse_id)
        
        # 检查是否有库存
        from app.models.warehouse import WarehouseStock
        stock_count = db.session.execute(
            select(db.func.count()).where(WarehouseStock.warehouse_id == warehouse_id)
        ).scalar()
        
        if stock_count > 0:
            raise BusinessError('仓库存在库存，无法删除', code=400)
        
        db.session.delete(warehouse)
        db.session.commit()
        
        logger.info('仓库删除成功', extra={'warehouse_id': warehouse_id})
    
    def get_locations(self, warehouse_id: int, page: int = 1, per_page: int = 50,
                     keyword: Optional[str] = None, location_type: Optional[str] = None) -> Dict[str, Any]:
        """获取库位列表"""
        query = select(WarehouseLocation).where(WarehouseLocation.warehouse_id == warehouse_id)
        
        if keyword:
            query = query.where(WarehouseLocation.code.ilike(f'%{keyword}%'))
        
        if location_type:
            query = query.where(WarehouseLocation.type == location_type)
        
        # 分页
        total = db.session.execute(select(db.func.count()).select_from(query.subquery())).scalar()
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        locations = db.session.execute(query).scalars().all()
        
        return {
            'items': locations,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    
    def create_location(self, warehouse_id: int, data: Dict[str, Any], 
                       user_id: Optional[int] = None) -> WarehouseLocation:
        """创建库位"""
        # 检查仓库是否存在
        warehouse = self.get_warehouse(warehouse_id)
        
        # 检查库位编码是否重复
        existing = db.session.execute(
            select(WarehouseLocation).where(
                and_(
                    WarehouseLocation.warehouse_id == warehouse_id,
                    WarehouseLocation.code == data['code']
                )
            )
        ).scalar_one_or_none()
        
        if existing:
            raise BusinessError(f'库位编码 {data["code"]} 已存在', code=400)
        
        # 创建库位 (v1.3 Updated)
        location = WarehouseLocation(
            warehouse_id=warehouse_id,
            code=data['code'],
            type=data.get('type', 'storage'),
            is_locked=data.get('is_locked', False),
            allow_mixing=data.get('allow_mixing', False)
        )
        
        db.session.add(location)
        db.session.commit()
        
        logger.info('库位创建成功', extra={
            'location_id': location.id,
            'warehouse_id': warehouse_id,
            'code': location.code,
            'created_by': user_id
        })
        
        return location
    
    def update_location(self, location_id: int, data: Dict[str, Any]) -> WarehouseLocation:
        """更新库位"""
        location = db.session.get(WarehouseLocation, location_id)
        if not location:
            raise BusinessError(f'库位 {location_id} 不存在', code=404)
        
        # 更新字段
        for key, value in data.items():
            if hasattr(location, key) and value is not None:
                setattr(location, key, value)
        
        db.session.commit()
        
        logger.info('库位更新成功', extra={
            'location_id': location_id,
            'updated_fields': list(data.keys())
        })
        
        return location
    
    def delete_location(self, location_id: int) -> None:
        """删除库位"""
        location = db.session.get(WarehouseLocation, location_id)
        if not location:
            raise BusinessError(f'库位 {location_id} 不存在', code=404)
        
        # 检查库位是否有库存
        from app.models.warehouse import WarehouseStockMovement
        movement_count = db.session.execute(
            select(db.func.count()).where(WarehouseStockMovement.location_id == location_id)
        ).scalar()
        
        if movement_count > 0:
            raise BusinessError('库位有库存流水记录，无法删除', code=400)
        
        db.session.delete(location)
        db.session.commit()
        
        logger.info('库位删除成功', extra={'location_id': location_id})
