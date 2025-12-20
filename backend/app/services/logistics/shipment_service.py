"""发货单服务层

负责发货单的业务逻辑：
- 发货单CRUD
- 自动计算金额（含税/不含税）
- 生成发货单号
- 按供应商拆分生成交付合同
- 生成报关单
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.logistics.shipment import ShipmentOrder, ShipmentOrderItem, ShipmentStatus
from app.errors import BusinessError

logger = logging.getLogger(__name__)


class ShipmentService:
    """发货单服务类"""
    
    @staticmethod
    def generate_shipment_no() -> str:
        """
        生成发货单号
        
        格式: SH-YYYYMMDD-NNNN
        例如: SH-20251218-0001
        """
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"SH-{today}"
        
        # 查询今天已有的最大流水号
        stmt = select(ShipmentOrder).where(
            ShipmentOrder.shipment_no.like(f"{prefix}%")
        ).order_by(ShipmentOrder.shipment_no.desc())
        
        last_shipment = db.session.execute(stmt).scalars().first()
        
        if last_shipment:
            # 提取流水号部分并加1
            last_no = last_shipment.shipment_no.split('-')[-1]
            next_no = int(last_no) + 1
        else:
            next_no = 1
        
        shipment_no = f"{prefix}-{next_no:04d}"
        logger.info(f'生成发货单号: {shipment_no}')
        
        return shipment_no
    
    @staticmethod
    def calculate_amounts(items: List[Dict[str, Any]]) -> Dict[str, Decimal]:
        """
        计算发货单总金额
        
        Args:
            items: 明细列表
            
        Returns:
            Dict: 包含total_amount, total_tax_amount, total_amount_with_tax
        """
        total_amount = Decimal('0')  # 不含税总额
        total_tax_amount = Decimal('0')  # 总税额
        total_amount_with_tax = Decimal('0')  # 含税总额
        
        for item in items:
            # 不含税金额
            item_total = Decimal(str(item.get('total_price', 0) or 0))
            total_amount += item_total
            
            # 税额
            item_tax = Decimal(str(item.get('tax_amount', 0) or 0))
            total_tax_amount += item_tax
            
            # 含税金额
            item_total_with_tax = Decimal(str(item.get('total_price_with_tax', 0) or 0))
            total_amount_with_tax += item_total_with_tax
        
        return {
            'total_amount': total_amount,
            'total_tax_amount': total_tax_amount,
            'total_amount_with_tax': total_amount_with_tax
        }
    
    @staticmethod
    def create_shipment(data: Dict[str, Any], created_by: Optional[int] = None) -> ShipmentOrder:
        """
        创建发货单
        
        Args:
            data: 发货单数据（包含items）
            created_by: 创建人ID
            
        Returns:
            ShipmentOrder: 创建的发货单对象
        """
        try:
            # 生成发货单号
            shipment_no = ShipmentService.generate_shipment_no()
            
            # 提取明细数据
            items_data = data.pop('items', [])
            
            if not items_data:
                raise BusinessError('发货明细不能为空', code=400)
            
            # 计算总金额（如果前端未提供）
            if 'total_amount' not in data or data['total_amount'] is None:
                amounts = ShipmentService.calculate_amounts(items_data)
                data.update(amounts)
            
            # 创建发货单主表
            shipment = ShipmentOrder(
                shipment_no=shipment_no,
                created_by=created_by,
                status=ShipmentStatus.DRAFT.value,
                **data
            )
            
            db.session.add(shipment)
            db.session.flush()  # 获取shipment.id
            
            # 创建明细
            for item_data in items_data:
                # 自动计算明细金额
                quantity = Decimal(str(item_data.get('quantity', 0)))
                unit_price = Decimal(str(item_data.get('unit_price', 0) or 0))
                tax_rate = Decimal(str(item_data.get('tax_rate', 0) or 0))
                
                # 不含税总价
                if 'total_price' not in item_data or item_data['total_price'] is None:
                    item_data['total_price'] = quantity * unit_price
                
                # 含税单价
                if 'unit_price_with_tax' not in item_data or item_data['unit_price_with_tax'] is None:
                    item_data['unit_price_with_tax'] = unit_price * (1 + tax_rate)
                
                # 税额
                if 'tax_amount' not in item_data or item_data['tax_amount'] is None:
                    item_data['tax_amount'] = item_data['total_price'] * tax_rate
                
                # 含税总价
                if 'total_price_with_tax' not in item_data or item_data['total_price_with_tax'] is None:
                    item_data['total_price_with_tax'] = item_data['total_price'] + item_data['tax_amount']
                
                item = ShipmentOrderItem(
                    shipment_id=shipment.id,
                    **item_data
                )
                db.session.add(item)
            
            db.session.commit()
            
            logger.info(f'创建发货单成功: {shipment_no}', extra={
                'shipment_id': shipment.id,
                'items_count': len(items_data),
                'total_amount': float(data.get('total_amount', 0))
            })
            
            # 重新查询以获取完整的关联数据
            return ShipmentService.get_shipment_by_id(shipment.id)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'创建发货单失败: {e}', exc_info=True)
            raise BusinessError(f'创建发货单失败: {str(e)}', code=500)
    
    @staticmethod
    def get_shipment_by_id(shipment_id: int) -> Optional[ShipmentOrder]:
        """
        根据ID获取发货单（预加载关联数据）
        
        Args:
            shipment_id: 发货单ID
            
        Returns:
            ShipmentOrder or None
        """
        stmt = select(ShipmentOrder).where(
            ShipmentOrder.id == shipment_id
        ).options(
            selectinload(ShipmentOrder.items),
            selectinload(ShipmentOrder.shipper_company),
            selectinload(ShipmentOrder.consignee),
            selectinload(ShipmentOrder.delivery_contracts),
            selectinload(ShipmentOrder.customs_declaration)
        )
        
        shipment = db.session.execute(stmt).scalars().first()
        return shipment
    
    @staticmethod
    def update_shipment(shipment_id: int, data: Dict[str, Any]) -> ShipmentOrder:
        """
        更新发货单
        
        Args:
            shipment_id: 发货单ID
            data: 更新数据
            
        Returns:
            ShipmentOrder: 更新后的发货单
        """
        shipment = ShipmentService.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise BusinessError('发货单不存在', code=404)
        
        # 检查状态是否允许修改
        if shipment.status not in [ShipmentStatus.DRAFT.value, ShipmentStatus.CONFIRMED.value]:
            raise BusinessError(f'发货单状态为{shipment.status}，不允许修改', code=400)
        
        try:
            # 更新字段
            for key, value in data.items():
                if hasattr(shipment, key) and key not in ['id', 'shipment_no', 'created_at', 'created_by']:
                    setattr(shipment, key, value)
            
            db.session.commit()
            
            logger.info(f'更新发货单成功: {shipment.shipment_no}', extra={
                'shipment_id': shipment_id
            })
            
            return ShipmentService.get_shipment_by_id(shipment_id)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'更新发货单失败: {e}', exc_info=True)
            raise BusinessError(f'更新发货单失败: {str(e)}', code=500)
    
    @staticmethod
    def delete_shipment(shipment_id: int) -> None:
        """
        删除发货单
        
        Args:
            shipment_id: 发货单ID
        """
        shipment = ShipmentService.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise BusinessError('发货单不存在', code=404)
        
        # 检查是否已生成关联单据
        if shipment.is_declared:
            raise BusinessError('发货单已生成报关单，不允许删除', code=400)
        
        if shipment.is_contracted:
            raise BusinessError('发货单已生成交付合同，不允许删除', code=400)
        
        # 只有草稿状态才允许删除
        if shipment.status != ShipmentStatus.DRAFT.value:
            raise BusinessError(f'只有草稿状态的发货单才能删除', code=400)
        
        try:
            db.session.delete(shipment)
            db.session.commit()
            
            logger.info(f'删除发货单成功: {shipment.shipment_no}', extra={
                'shipment_id': shipment_id
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'删除发货单失败: {e}', exc_info=True)
            raise BusinessError(f'删除发货单失败: {str(e)}', code=500)
    
    @staticmethod
    def confirm_shipment(shipment_id: int) -> ShipmentOrder:
        """
        确认发货单（从草稿变为确认状态）
        
        Args:
            shipment_id: 发货单ID
            
        Returns:
            ShipmentOrder: 更新后的发货单
        """
        shipment = ShipmentService.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise BusinessError('发货单不存在', code=404)
        
        if shipment.status != ShipmentStatus.DRAFT.value:
            raise BusinessError(f'只有草稿状态的发货单才能确认', code=400)
        
        # 检查必填字段
        if not shipment.items or len(shipment.items) == 0:
            raise BusinessError('发货单明细不能为空', code=400)
        
        try:
            shipment.status = ShipmentStatus.CONFIRMED.value
            db.session.commit()
            
            logger.info(f'确认发货单成功: {shipment.shipment_no}', extra={
                'shipment_id': shipment_id
            })
            
            return ShipmentService.get_shipment_by_id(shipment_id)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'确认发货单失败: {e}', exc_info=True)
            raise BusinessError(f'确认发货单失败: {str(e)}', code=500)
    
    @staticmethod
    def get_suppliers_from_shipment(shipment_id: int) -> List[Dict[str, Any]]:
        """
        获取发货单中涉及的所有供应商及其对应的商品
        
        用于预览按供应商拆分的结果
        
        Args:
            shipment_id: 发货单ID
            
        Returns:
            List[Dict]: 供应商列表，每个包含supplier_id和items
        """
        shipment = ShipmentService.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise BusinessError('发货单不存在', code=404)
        
        # 按供应商分组
        supplier_groups = {}
        
        for item in shipment.items:
            supplier_id = item.supplier_id
            
            if not supplier_id:
                raise BusinessError(
                    f'商品"{item.product_name}"未指定供应商，无法拆分',
                    code=400
                )
            
            if supplier_id not in supplier_groups:
                supplier_groups[supplier_id] = {
                    'supplier_id': supplier_id,
                    'supplier_name': item.supplier.name if item.supplier else None,
                    'items': [],
                    'total_amount': Decimal('0'),
                    'total_quantity': 0
                }
            
            supplier_groups[supplier_id]['items'].append({
                'sku': item.sku,
                'product_name': item.product_name,
                'quantity': float(item.quantity),
                'unit': item.unit,
                'unit_price': float(item.unit_price or 0),
                'total_price': float(item.total_price or 0),
                'total_price_with_tax': float(item.total_price_with_tax or 0)
            })
            
            supplier_groups[supplier_id]['total_amount'] += (item.total_price or Decimal('0'))
            supplier_groups[supplier_id]['total_quantity'] += 1
        
        result = list(supplier_groups.values())
        
        logger.info(f'发货单{shipment.shipment_no}涉及{len(result)}个供应商')
        
        return result
