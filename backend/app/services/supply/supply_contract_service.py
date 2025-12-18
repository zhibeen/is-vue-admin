"""开票合同服务 - 双轨制合同核心逻辑"""
import logging
from typing import Optional
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.supply.delivery import ScmDeliveryContract
from app.models.supply.supply_contract import ScmSupplyContract, ScmSupplyContractItem
from app.services.serc.common import generate_seq_no
from app.errors import BusinessError

logger = logging.getLogger(__name__)


class SupplyContractService:
    """开票合同服务类"""
    
    @staticmethod
    def create_supply_contract(
        data: dict,
        created_by: Optional[int] = None
    ) -> ScmSupplyContract:
        """
        创建开票合同
        
        支持两种模式：
        1. auto模式：自动复制交付合同（品名/数量/单位完全一致）
        2. manual模式：手工调整品名/数量/单位（但总金额必须一致）
        
        Args:
            data: 开票合同数据
            created_by: 创建人ID
            
        Returns:
            ScmSupplyContract: 创建的开票合同
        """
        try:
            delivery_contract_id = data.get('delivery_contract_id')
            mode = data.get('mode', 'auto')
            
            if not delivery_contract_id:
                raise BusinessError('必须指定交付合同ID')
            
            # 查询交付合同
            delivery_contract = SupplyContractService._get_delivery_contract(delivery_contract_id)
            
            # 检查是否已生成开票合同（严格1对1）
            existing = db.session.execute(
                select(ScmSupplyContract).where(
                    ScmSupplyContract.delivery_contract_id == delivery_contract_id
                )
            ).scalar_one_or_none()
            
            if existing:
                raise BusinessError(
                    f'交付合同{delivery_contract.contract_no}已生成开票合同'
                    f'{existing.contract_no}，禁止重复开票'
                )
            
            # 根据模式生成开票合同
            if mode == 'auto':
                supply_contract = SupplyContractService._create_auto_mode(
                    delivery_contract=delivery_contract,
                    data=data,
                    created_by=created_by
                )
            else:
                supply_contract = SupplyContractService._create_manual_mode(
                    delivery_contract=delivery_contract,
                    data=data,
                    created_by=created_by
                )
            
            # 更新交付合同状态
            delivery_contract.has_supply_contract = True
            
            db.session.commit()
            
            logger.info(
                f"创建开票合同成功: {supply_contract.contract_no} (模式: {mode})",
                extra={
                    'supply_contract_id': supply_contract.id,
                    'delivery_contract_id': delivery_contract_id,
                    'mode': mode
                }
            )
            
            return supply_contract
            
        except BusinessError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建开票合同失败: {str(e)}", exc_info=True)
            raise BusinessError(f'创建开票合同失败: {str(e)}')
    
    @staticmethod
    def _get_delivery_contract(delivery_contract_id: int) -> ScmDeliveryContract:
        """查询交付合同（含明细）"""
        stmt = select(ScmDeliveryContract).options(
            selectinload(ScmDeliveryContract.items)
        ).where(ScmDeliveryContract.id == delivery_contract_id)
        
        delivery_contract = db.session.execute(stmt).scalar_one_or_none()
        
        if not delivery_contract:
            raise BusinessError(f'交付合同不存在: ID={delivery_contract_id}')
        
        return delivery_contract
    
    @staticmethod
    def _create_auto_mode(
        delivery_contract: ScmDeliveryContract,
        data: dict,
        created_by: Optional[int]
    ) -> ScmSupplyContract:
        """
        自动模式：完全复制交付合同
        
        品名、数量、单位完全一致，仅添加税率信息
        """
        # 生成合同号
        contract_no = generate_seq_no('SC', db)
        
        # 计算含税金额
        tax_rate = Decimal(str(data.get('tax_rate', 0.13)))  # 默认13%
        total_amount = delivery_contract.total_amount
        total_amount_with_tax = total_amount * (1 + tax_rate)
        
        # 创建开票合同
        supply_contract = ScmSupplyContract(
            contract_no=contract_no,
            delivery_contract_id=delivery_contract.id,
            supplier_id=delivery_contract.supplier_id,
            total_amount=total_amount,
            currency=delivery_contract.currency,
            tax_rate=tax_rate,
            total_amount_with_tax=total_amount_with_tax,
            status='confirmed',
            invoice_status='uninvoiced',
            invoiced_amount=Decimal('0'),
            contract_date=data.get('contract_date'),
            notes='自动生成（品名/数量与交付合同一致）',
            created_by=created_by
        )
        
        # 复制明细
        for dc_item in delivery_contract.items:
            # 获取产品名称
            product_name = (
                dc_item.product.name if dc_item.product else '未知商品'
            )
            
            # 计算税额
            tax_amount = dc_item.total_price * tax_rate
            
            sc_item = ScmSupplyContractItem(
                product_name=product_name,
                specification='',
                quantity=dc_item.confirmed_qty,
                unit='个',  # TODO: 从产品获取单位
                unit_price=dc_item.unit_price,
                total_price=dc_item.total_price,
                tax_amount=tax_amount,
                source_delivery_item_ids={'ids': [dc_item.id]}
            )
            supply_contract.items.append(sc_item)
        
        db.session.add(supply_contract)
        
        logger.info(f"自动模式生成开票合同: {contract_no}")
        
        return supply_contract
    
    @staticmethod
    def _create_manual_mode(
        delivery_contract: ScmDeliveryContract,
        data: dict,
        created_by: Optional[int]
    ) -> ScmSupplyContract:
        """
        手工模式：允许调整品名/数量/单位
        
        关键约束：
        1. 总金额必须与交付合同一致
        2. 必须填写调整说明（notes）
        """
        items_data = data.get('items', [])
        
        if not items_data:
            raise BusinessError('手工模式必须提供明细数据')
        
        if not data.get('notes'):
            raise BusinessError('手工调整品名/数量时必须填写业务说明')
        
        # 计算开票合同总金额
        supply_total = sum(
            Decimal(str(item.get('total_price', 0)))
            for item in items_data
        )
        
        # 金额一致性校验（严格1对1的核心约束）
        delivery_total = delivery_contract.total_amount
        if abs(supply_total - delivery_total) > Decimal('0.01'):
            raise BusinessError(
                f'开票合同总金额({supply_total})必须与交付合同总金额({delivery_total})一致'
            )
        
        # 生成合同号
        contract_no = generate_seq_no('SC', db)
        
        # 计算含税金额
        tax_rate = Decimal(str(data.get('tax_rate', 0.13)))
        total_amount_with_tax = supply_total * (1 + tax_rate)
        
        # 创建开票合同
        supply_contract = ScmSupplyContract(
            contract_no=contract_no,
            delivery_contract_id=delivery_contract.id,
            supplier_id=delivery_contract.supplier_id,
            total_amount=supply_total,
            currency=delivery_contract.currency,
            tax_rate=tax_rate,
            total_amount_with_tax=total_amount_with_tax,
            status='confirmed',
            invoice_status='uninvoiced',
            invoiced_amount=Decimal('0'),
            contract_date=data.get('contract_date'),
            notes=data.get('notes'),
            created_by=created_by
        )
        
        # 创建明细
        for item_data in items_data:
            tax_amount = Decimal(str(item_data.get('total_price', 0))) * tax_rate
            
            sc_item = ScmSupplyContractItem(
                product_name=item_data.get('product_name'),
                specification=item_data.get('specification', ''),
                quantity=Decimal(str(item_data.get('quantity'))),
                unit=item_data.get('unit'),
                unit_price=Decimal(str(item_data.get('unit_price'))),
                total_price=Decimal(str(item_data.get('total_price'))),
                tax_amount=tax_amount,
                source_delivery_item_ids=item_data.get('source_delivery_item_ids', {})
            )
            supply_contract.items.append(sc_item)
        
        db.session.add(supply_contract)
        
        logger.info(f"手工模式生成开票合同: {contract_no}")
        
        return supply_contract
    
    @staticmethod
    def get_supply_contract_by_id(contract_id: int) -> Optional[ScmSupplyContract]:
        """根据ID查询开票合同（含明细）"""
        stmt = select(ScmSupplyContract).options(
            selectinload(ScmSupplyContract.items),
            selectinload(ScmSupplyContract.delivery_contract)
        ).where(ScmSupplyContract.id == contract_id)
        
        return db.session.execute(stmt).scalar_one_or_none()

