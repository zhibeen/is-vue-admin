from app.models.warehouse import Warehouse, WarehouseStock, WarehouseStockDiscrepancy
from app.errors import BusinessError
import logging
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from app.extensions import db
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SyncService:
    """库存同步服务"""
    
    def __init__(self):
        pass
    
    def sync_inventory(self, warehouse_id: int) -> Dict[str, Any]:
        """
        触发库存同步
        1. 获取仓库配置 (API Config)
        2. 调用第三方 API 获取库存快照
        3. 对比本地库存
        4. 生成差异单 (Discrepancy)
        """
        warehouse = db.session.get(Warehouse, warehouse_id)
        if not warehouse:
            raise BusinessError(f'仓库 {warehouse_id} 不存在', code=404)
            
        if warehouse.ownership_type != 'third_party':
            raise BusinessError('仅支持第三方仓库同步', code=400)
            
        # Mock Third Party API Call
        # 实际应调用 adapter pattern 封装的外部服务
        external_inventory = self._mock_fetch_external_inventory(warehouse)
        
        stats = {
            'total': len(external_inventory),
            'matched': 0,
            'discrepancy': 0,
            'new': 0
        }
        
        for item in external_inventory:
            sku = item['sku']
            remote_qty = item['quantity']
            
            # Get Local Stock
            local_stock = db.session.execute(
                select(WarehouseStock).where(
                    and_(
                        WarehouseStock.warehouse_id == warehouse_id,
                        WarehouseStock.sku == sku
                    )
                )
            ).scalar_one_or_none()
            
            local_qty = local_stock.physical_quantity if local_stock else 0
            
            if local_qty != remote_qty:
                # Record Discrepancy
                self._record_discrepancy({
                    'warehouse_id': warehouse_id,
                    'sku': sku,
                    'local_qty': local_qty,
                    'remote_qty': remote_qty,
                    'diff_ratio': 0.0, # Todo calc
                    'diff_amount': 0.0 # Todo calc
                })
                stats['discrepancy'] += 1
            else:
                stats['matched'] += 1
                
        db.session.commit()
        return stats

    def _mock_fetch_external_inventory(self, warehouse: Warehouse) -> List[Dict[str, Any]]:
        """Mock data"""
        return [
            {'sku': 'SKU001', 'quantity': 100},
            {'sku': 'SKU002', 'quantity': 50},
            {'sku': 'SKU003', 'quantity': 0}
        ]

    def _record_discrepancy(self, discrepancy_data: Dict[str, Any]) -> WarehouseStockDiscrepancy:
        """记录差异"""
        # Check if pending discrepancy exists
        existing = db.session.execute(
            select(WarehouseStockDiscrepancy).where(
                and_(
                    WarehouseStockDiscrepancy.warehouse_id == discrepancy_data['warehouse_id'],
                    WarehouseStockDiscrepancy.sku == discrepancy_data['sku'],
                    WarehouseStockDiscrepancy.status == 'pending'
                )
            )
        ).scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.local_qty = discrepancy_data['local_qty']
            existing.remote_qty = discrepancy_data['remote_qty']
            existing.updated_at = datetime.utcnow()
            return existing
        else:
            # Create new
            discrepancy = WarehouseStockDiscrepancy(
                warehouse_id=discrepancy_data['warehouse_id'],
                sku=discrepancy_data['sku'],
                local_qty=discrepancy_data['local_qty'],
                remote_qty=discrepancy_data['remote_qty'],
                status='pending'
            )
            db.session.add(discrepancy)
            return discrepancy

    def get_discrepancy_list(self, page: int = 1, per_page: int = 20,
                            warehouse_id: Optional[int] = None, sku: Optional[str] = None,
                            status: Optional[str] = None,
                            start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取差异列表"""
        query = select(WarehouseStockDiscrepancy).options(joinedload(WarehouseStockDiscrepancy.warehouse))
        
        if warehouse_id:
            query = query.where(WarehouseStockDiscrepancy.warehouse_id == warehouse_id)
            
        if sku:
            query = query.where(WarehouseStockDiscrepancy.sku.ilike(f'%{sku}%'))
            
        if status:
            query = query.where(WarehouseStockDiscrepancy.status == status)
            
        if start_date:
            query = query.where(WarehouseStockDiscrepancy.created_at >= start_date)
            
        if end_date:
            query = query.where(WarehouseStockDiscrepancy.created_at <= end_date)
            
        query = query.order_by(WarehouseStockDiscrepancy.discovered_at.desc())
        
        # 分页
        total = db.session.execute(select(func.count()).select_from(query.subquery())).scalar()
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        items = db.session.execute(query).scalars().all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page
        }

    def resolve_discrepancy(self, discrepancy_id: int, resolution_type: str, 
                           note: Optional[str] = None, 
                           user_id: Optional[int] = None) -> WarehouseStockDiscrepancy:
        """处理差异"""
        discrepancy = db.session.get(WarehouseStockDiscrepancy, discrepancy_id)
        if not discrepancy:
            raise BusinessError(f'差异单 {discrepancy_id} 不存在', code=404)
            
        if discrepancy.status != 'pending':
            raise BusinessError('差异单已处理', code=400)
            
        if resolution_type == 'adjust_local':
            # 生成调整单，以远程库存为准
            self._create_adjustment_from_discrepancy(discrepancy, user_id)
            discrepancy.resolution = 'Adjusted to match remote'
        elif resolution_type == 'ignore':
            discrepancy.resolution = 'Ignored'
        else:
            raise BusinessError(f'不支持的处理类型: {resolution_type}', code=400)
            
        discrepancy.status = 'resolved'
        discrepancy.resolved_at = datetime.utcnow()
        discrepancy.resolver_id = user_id
        if note:
            discrepancy.resolution += f" - {note}"
            
        db.session.commit()
        return discrepancy

    def _create_adjustment_from_discrepancy(self, discrepancy: WarehouseStockDiscrepancy, user_id: Optional[int] = None) -> None:
        """生成调整单"""
        from app.services.warehouse.stock_service import StockService
        
        stock_service = StockService()
        
        diff = discrepancy.remote_qty - discrepancy.local_qty
        if diff == 0:
            return
            
        stock_service.adjust_stock({
            'sku': discrepancy.sku,
            'warehouse_id': discrepancy.warehouse_id,
            'quantity': diff,
            'type': 'adjustment', # system adjustment
            'order_no': f'DISC-{discrepancy.id}',
            'reason': 'Sync Discrepancy Adjustment'
        }, user_id=user_id)

def sync_all_third_party_warehouses():
    """Sync all 3rd party warehouses (Task Entry Point)"""
    # Import locally to avoid circular import if needed, 
    # but here it's likely fine as we are in service layer.
    # However, to use db, we need app context if running as script, 
    # but as Celery task, we have it.
    
    # 1. Find all 3rd party warehouses
    warehouses = db.session.execute(
        select(Warehouse).where(Warehouse.ownership_type == 'third_party')
    ).scalars().all()
    
    service = SyncService()
    results = {}
    
    for wh in warehouses:
        try:
            logger.info(f"Starting sync for warehouse {wh.name} (ID: {wh.id})...")
            stats = service.sync_inventory(wh.id)
            results[wh.code] = {'status': 'success', 'stats': stats}
        except Exception as e:
            logger.error(f"Failed to sync warehouse {wh.id}: {str(e)}")
            results[wh.code] = {'status': 'error', 'message': str(e)}
            
    return results
