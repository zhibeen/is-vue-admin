"""发货单服务 - 核心业务逻辑"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.logistics.shipment import ShipmentOrder, ShipmentOrderItem, ShipmentStatus
from app.models.supply.delivery import ScmDeliveryContract, ScmDeliveryContractItem
from app.services.serc.common import generate_seq_no
from app.errors import BusinessError

logger = logging.getLogger(__name__)


class ShipmentService:
    """发货单服务类"""
    
    @staticmethod
    def create_shipment(data: dict, created_by: Optional[int] = None) -> ShipmentOrder:
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
            shipment_no = generate_seq_no('SH', db)
            
            # 提取明细数据
            items_data = data.pop('items', [])
            
            # 创建发货单主记录
            shipment = ShipmentOrder(
                shipment_no=shipment_no,
                status=ShipmentStatus.DRAFT.value,
                created_by=created_by,
                **data
            )
            
            # 创建明细
            for item_data in items_data:
                item = ShipmentOrderItem(**item_data)
                shipment.items.append(item)
            
            # 计算汇总信息（如果未提供）
            if not shipment.total_amount and items_data:
                shipment.total_amount = sum(
                    Decimal(str(item.get('total_price', 0) or 0))
                    for item in items_data
                )
            
            if not shipment.total_net_weight and items_data:
                shipment.total_net_weight = sum(
                    Decimal(str(item.get('total_weight', 0) or 0))
                    for item in items_data
                )
            
            db.session.add(shipment)
            db.session.commit()
            
            logger.info(
                f"创建发货单成功: {shipment.shipment_no}",
                extra={'shipment_id': shipment.id, 'user_id': created_by}
            )
            
            return shipment
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建发货单失败: {str(e)}", exc_info=True)
            raise BusinessError(f'创建发货单失败: {str(e)}')
    
    @staticmethod
    def generate_delivery_contracts(
        shipment_id: int,
        created_by: Optional[int] = None
    ) -> List[ScmDeliveryContract]:
        """
        从发货单按供应商自动拆分生成交付合同
        
        核心逻辑：
        1. 按 supplier_id 分组发货明细
        2. 为每个供应商创建一个独立的交付合同
        3. 更新发货单的 is_contracted 状态
        
        Args:
            shipment_id: 发货单ID
            created_by: 创建人ID
            
        Returns:
            List[ScmDeliveryContract]: 生成的交付合同列表
        """
        try:
            # 查询发货单（预加载明细）
            stmt = select(ShipmentOrder).options(
                selectinload(ShipmentOrder.items)
            ).where(ShipmentOrder.id == shipment_id)
            
            shipment = db.session.execute(stmt).scalar_one_or_none()
            
            if not shipment:
                raise BusinessError(f'发货单不存在: ID={shipment_id}')
            
            if shipment.is_contracted:
                raise BusinessError(f'发货单已生成交付合同，禁止重复生成')
            
            if not shipment.items:
                raise BusinessError(f'发货单没有明细，无法生成交付合同')
            
            # 按供应商分组
            supplier_groups = defaultdict(list)
            for item in shipment.items:
                if not item.supplier_id:
                    raise BusinessError(
                        f'发货明细 SKU={item.sku} 未指定供应商，无法自动拆分'
                    )
                supplier_groups[item.supplier_id].append(item)
            
            logger.info(
                f"发货单按供应商拆分: {len(supplier_groups)}个供应商",
                extra={'shipment_id': shipment_id, 'supplier_count': len(supplier_groups)}
            )
            
            # 为每个供应商生成交付合同
            contracts = []
            for supplier_id, items in supplier_groups.items():
                contract = ShipmentService._create_delivery_contract_for_supplier(
                    shipment=shipment,
                    supplier_id=supplier_id,
                    items=items,
                    created_by=created_by
                )
                contracts.append(contract)
            
            # 更新发货单状态
            shipment.is_contracted = True
            shipment.status = ShipmentStatus.CONFIRMED.value
            
            db.session.commit()
            
            logger.info(
                f"成功生成{len(contracts)}个交付合同",
                extra={'shipment_id': shipment_id, 'contract_count': len(contracts)}
            )
            
            return contracts
            
        except BusinessError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"生成交付合同失败: {str(e)}", exc_info=True)
            raise BusinessError(f'生成交付合同失败: {str(e)}')
    
    @staticmethod
    def _create_delivery_contract_for_supplier(
        shipment: ShipmentOrder,
        supplier_id: int,
        items: List[ShipmentOrderItem],
        created_by: Optional[int] = None
    ) -> ScmDeliveryContract:
        """
        为单个供应商创建交付合同
        
        Args:
            shipment: 发货单对象
            supplier_id: 供应商ID
            items: 该供应商的明细列表
            created_by: 创建人ID
            
        Returns:
            ScmDeliveryContract: 创建的交付合同
        """
        # 生成合同号
        contract_no = generate_seq_no('DC', db)
        
        # 计算总金额
        total_amount = sum(
            item.total_price or Decimal('0')
            for item in items
        )
        
        # 创建交付合同
        contract = ScmDeliveryContract(
            contract_no=contract_no,
            shipment_id=shipment.id,
            supplier_id=supplier_id,
            company_id=shipment.shipper_company_id,
            total_amount=total_amount,
            currency='CNY',  # 国内采购默认人民币
            status='confirmed',
            delivery_date=datetime.now().date(),
            has_supply_contract=False
        )
        
        # 创建合同明细
        for shipment_item in items:
            contract_item = ScmDeliveryContractItem(
                product_id=shipment_item.product_id,
                confirmed_qty=shipment_item.quantity,
                unit_price=shipment_item.unit_price or Decimal('0'),
                total_price=shipment_item.total_price or Decimal('0'),
                notes=f'来源发货单: {shipment.shipment_no}, SKU: {shipment_item.sku}'
            )
            contract.items.append(contract_item)
        
        db.session.add(contract)
        
        logger.info(
            f"为供应商创建交付合同: {contract_no}",
            extra={
                'supplier_id': supplier_id,
                'item_count': len(items),
                'total_amount': float(total_amount)
            }
        )
        
        return contract
    
    @staticmethod
    def get_shipment_by_id(shipment_id: int) -> Optional[ShipmentOrder]:
        """根据ID查询发货单（含明细）"""
        stmt = select(ShipmentOrder).options(
            selectinload(ShipmentOrder.items),
            selectinload(ShipmentOrder.delivery_contracts)
        ).where(ShipmentOrder.id == shipment_id)
        
        return db.session.execute(stmt).scalar_one_or_none()
    
    @staticmethod
    def update_shipment(shipment_id: int, data: dict) -> ShipmentOrder:
        """更新发货单"""
        shipment = ShipmentService.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise BusinessError(f'发货单不存在: ID={shipment_id}')
        
        if shipment.is_contracted:
            raise BusinessError('发货单已生成交付合同，禁止修改')
        
        # 更新字段
        for key, value in data.items():
            if hasattr(shipment, key):
                setattr(shipment, key, value)
        
        db.session.commit()
        
        return shipment
    
    @staticmethod
    def delete_shipment(shipment_id: int):
        """删除发货单"""
        shipment = ShipmentService.get_shipment_by_id(shipment_id)
        
        if not shipment:
            raise BusinessError(f'发货单不存在: ID={shipment_id}')
        
        if shipment.is_contracted:
            raise BusinessError('发货单已生成交付合同，禁止删除')
        
        if shipment.is_declared:
            raise BusinessError('发货单已生成报关单，禁止删除')
        
        db.session.delete(shipment)
        db.session.commit()
        
        logger.info(f"删除发货单: {shipment.shipment_no}", extra={'shipment_id': shipment_id})

