from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
from app.extensions import db
from app.models.warehouse import WarehouseStock, WarehouseStockMovement, Warehouse
from app.errors import BusinessError
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StockService:
    """库存服务"""
    
    def __init__(self):
        pass
    
    # 移除 data_permission_filter 装饰器，暂时不使用数据权限过滤
    def get_stock_list(self, page: int = 1, per_page: int = 20, 
                      sku: Optional[str] = None, warehouse_id: Optional[int] = None,
                      batch_no: Optional[str] = None, min_quantity: Optional[int] = None,
                      max_quantity: Optional[int] = None) -> Dict[str, Any]:
        """获取库存列表"""
        query = select(WarehouseStock).options(joinedload(WarehouseStock.warehouse))
        
        # 搜索条件
        if sku:
            query = query.where(WarehouseStock.sku.ilike(f'%{sku}%'))
        
        if warehouse_id:
            query = query.where(WarehouseStock.warehouse_id == warehouse_id)
        
        if batch_no:
            query = query.where(WarehouseStock.batch_no.ilike(f'%{batch_no}%'))
        
        if min_quantity is not None:
            query = query.where(WarehouseStock.available_quantity >= min_quantity)
        
        if max_quantity is not None:
            query = query.where(WarehouseStock.available_quantity <= max_quantity)
        
        # 分页
        total = db.session.execute(select(func.count()).select_from(query.subquery())).scalar()
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        # 执行查询
        stocks = db.session.execute(query).scalars().all()
        
        return {
            'items': stocks,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    
    def get_stock(self, sku: str, warehouse_id: int) -> WarehouseStock:
        
        stock = db.session.execute(
            select(WarehouseStock).where(
                and_(
                    WarehouseStock.sku == sku,
                    WarehouseStock.warehouse_id == warehouse_id
                )
            )
        ).scalar_one_or_none()
        
        if not stock:
            # 如果不存在，创建一条空记录
            stock = WarehouseStock(
                sku=sku,
                warehouse_id=warehouse_id,
                physical_quantity=0,
                available_quantity=0,
                allocated_quantity=0,
                in_transit_quantity=0,
                damaged_quantity=0
            )
            db.session.add(stock)
            db.session.commit()
        
        return stock
    
    def adjust_stock(self, data: Dict[str, Any], user_id: Optional[int] = None) -> WarehouseStock:
        """调整库存"""
        stock = self.get_stock(data['sku'], data['warehouse_id'])
        
        # 创建库存流水
        movement = WarehouseStockMovement(
            sku=stock.sku,
            warehouse_id=stock.warehouse_id,
            location_id=data.get('location_id'),
            order_type=data.get('type'), # inbound, outbound, adjustment
            order_no=data.get('order_no', f'ADJ-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}'),
            quantity_delta=data['quantity'],
            batch_no=data.get('batch_no'),
            unit_cost=data.get('unit_cost'),
            currency=data.get('currency'),
            created_by=user_id
        )
        
        db.session.add(movement)
        
        # 更新库存
        # 使用乐观锁
        count = db.session.execute(
            db.update(WarehouseStock).where(
                and_(
                    WarehouseStock.id == stock.id,
                    WarehouseStock.version == stock.version
                )
            ).values(
                physical_quantity=WarehouseStock.physical_quantity + data['quantity'],
                available_quantity=WarehouseStock.available_quantity + data['quantity'],
                version=WarehouseStock.version + 1,
                updated_at=datetime.utcnow()
            )
        ).rowcount
        
        if count == 0:
            raise BusinessError('库存已被修改，请重试', code=409)
        
        db.session.commit()
        db.session.refresh(stock)
        
        logger.info('库存调整成功', extra={
            'stock_id': stock.id,
            'sku': stock.sku,
            'warehouse_id': stock.warehouse_id,
            'quantity': data['quantity'],
            'type': data.get('type'),
            'user_id': user_id
        })
        
        return stock 

    def get_movement_list(self, page: int = 1, per_page: int = 20,
                         sku: Optional[str] = None, warehouse_id: Optional[int] = None,
                         order_type: Optional[str] = None, order_no: Optional[str] = None,
                         start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取库存流水列表"""
        query = select(WarehouseStockMovement).options(
            joinedload(WarehouseStockMovement.warehouse),
            joinedload(WarehouseStockMovement.location)
        )
        
        if sku:
            query = query.where(WarehouseStockMovement.sku == sku)
        
        if warehouse_id:
            query = query.where(WarehouseStockMovement.warehouse_id == warehouse_id)
            
        if order_type:
            query = query.where(WarehouseStockMovement.order_type == order_type)
            
        if order_no:
            query = query.where(WarehouseStockMovement.order_no.ilike(f'%{order_no}%'))
            
        if start_date:
            query = query.where(WarehouseStockMovement.created_at >= start_date)
            
        if end_date:
            query = query.where(WarehouseStockMovement.created_at <= end_date)
            
        query = query.order_by(WarehouseStockMovement.created_at.desc())
        
        # 分页
        total = db.session.execute(select(func.count()).select_from(query.subquery())).scalar()
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        movements = db.session.execute(query).scalars().all()
        
        return {
            'items': movements,
            'total': total,
            'page': page,
            'per_page': per_page
        }

    def get_summary(self, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """获取库存汇总"""
        query = select(
            func.sum(WarehouseStock.physical_quantity).label('total_physical'),
            func.sum(WarehouseStock.available_quantity).label('total_available'),
            func.sum(WarehouseStock.allocated_quantity).label('total_allocated'),
            func.sum(WarehouseStock.in_transit_quantity).label('total_in_transit'),
            func.sum(WarehouseStock.damaged_quantity).label('total_damaged'),
            func.count(WarehouseStock.id).label('sku_count')
        )
        
        if warehouse_id:
            query = query.where(WarehouseStock.warehouse_id == warehouse_id)
            
        result = db.session.execute(query).one()
        
        return {
            'total_physical': result.total_physical or 0,
            'total_available': result.total_available or 0,
            'total_allocated': result.total_allocated or 0,
            'total_in_transit': result.total_in_transit or 0,
            'total_damaged': result.total_damaged or 0,
            'sku_count': result.sku_count or 0
        }

    def allocate_stock(self, sku: str, warehouse_id: int, quantity: int) -> WarehouseStock:
        """分配/锁定库存"""
        # 1. 检查库存是否充足
        stock = self.get_stock(sku, warehouse_id)
        
        if stock.available_quantity < quantity:
            raise BusinessError(f'库存不足 (可用: {stock.available_quantity}, 需要: {quantity})', code=400)
            
        # 2. 更新库存 (Available - qty, Allocated + qty)
        count = db.session.execute(
            db.update(WarehouseStock).where(
                and_(
                    WarehouseStock.sku == sku,
                    WarehouseStock.warehouse_id == warehouse_id,
                    WarehouseStock.version == stock.version
                )
            ).values(
                available_quantity=WarehouseStock.available_quantity - quantity,
                allocated_quantity=WarehouseStock.allocated_quantity + quantity,
                version=WarehouseStock.version + 1,
                updated_at=datetime.utcnow()
            )
        ).rowcount
        
        if count == 0:
            raise BusinessError('库存已被修改，请重试', code=409)
            
        db.session.commit()
        db.session.refresh(stock)
        return stock

    def release_stock(self, sku: str, warehouse_id: int, quantity: int) -> WarehouseStock:
        """释放已分配库存"""
        stock = self.get_stock(sku, warehouse_id)
        
        if stock.allocated_quantity < quantity:
             raise BusinessError(f'释放数量超过已分配数量 (已分配: {stock.allocated_quantity})', code=400)

        # 2. 更新库存 (Available + qty, Allocated - qty)
        count = db.session.execute(
            db.update(WarehouseStock).where(
                and_(
                    WarehouseStock.sku == sku,
                    WarehouseStock.warehouse_id == warehouse_id,
                    WarehouseStock.version == stock.version
                )
            ).values(
                available_quantity=WarehouseStock.available_quantity + quantity,
                allocated_quantity=WarehouseStock.allocated_quantity - quantity,
                version=WarehouseStock.version + 1,
                updated_at=datetime.utcnow()
            )
        ).rowcount
        
        if count == 0:
            raise BusinessError('库存已被修改，请重试', code=409)
            
        db.session.commit()
        db.session.refresh(stock)
        return stock