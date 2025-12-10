from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_
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
    
    # 移除 data_permission_filter 装饰器，暂时不使用数据权限过滤
    def get_list(self, page: int = 1, per_page: int = 20, keyword: Optional[str] = None, 
                 category: Optional[str] = None, location_type: Optional[str] = None,
                 ownership_type: Optional[str] = None) -> Dict[str, Any]:
        """获取仓库列表"""
        query = select(Warehouse)
        
        # 搜索条件
        if keyword:
            query = query.where(
                or_(
                    Warehouse.code.ilike(f'%{keyword}%'),
                    Warehouse.name.ilike(f'%{keyword}%')
                )
            )
        
        if category:
            query = query.where(Warehouse.category == category)
        
        if location_type:
            query = query.where(Warehouse.location_type == location_type)
        
        if ownership_type:
            query = query.where(Warehouse.ownership_type == ownership_type)
        
        # 分页
        total = db.session.execute(select(db.func.count()).select_from(query.subquery())).scalar()
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        # 执行查询
        warehouses = db.session.execute(query).scalars().all()
        
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
    
    def create_warehouse(self, data: Dict[str, Any], user_id: Optional[int] = None) -> Warehouse:
        """创建仓库"""
        # 检查编码是否重复
        existing = db.session.execute(
            select(Warehouse).where(Warehouse.code == data['code'])
        ).scalar_one_or_none()
        
        if existing:
            raise BusinessError(f'仓库编码 {data["code"]} 已存在', code=400)
        
        # 创建仓库
        warehouse = Warehouse(
            code=data['code'],
            name=data['name'],
            category=data['category'],
            location_type=data['location_type'],
            ownership_type=data['ownership_type'],
            business_type=data.get('business_type', 'standard'),
            currency=data.get('currency', 'USD'),
            capacity=data.get('capacity'),
            max_volume=data.get('max_volume'),
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
        
        # 更新字段
        for key, value in data.items():
            if hasattr(warehouse, key) and value is not None:
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
        
        # 创建库位
        location = WarehouseLocation(
            warehouse_id=warehouse_id,
            code=data['code'],
            type=data.get('type', 'storage'),
            max_quantity=data.get('max_quantity'),
            max_weight=data.get('max_weight'),
            max_volume=data.get('max_volume'),
            created_by=user_id
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
