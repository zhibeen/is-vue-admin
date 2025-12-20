"""发货单采购明细服务层

核心逻辑：
1. 采购明细是唯一的价格数据源
2. 商品明细通过采购明细自动汇总生成
3. 数据一致性验证
"""
from typing import List, Dict, Optional
from decimal import Decimal
from collections import Counter
from sqlalchemy import func
from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models.logistics.purchase_item import ShipmentPurchaseItem
from app.models.logistics.shipment import ShipmentOrderItem, ShipmentOrder
from app.models.product import ProductVariant
from app.errors import BusinessError


class ShipmentPurchaseItemService:
    """采购明细服务"""
    
    @staticmethod
    def create_purchase_item(shipment_id: int, data: dict) -> ShipmentPurchaseItem:
        """
        创建采购明细
        
        创建后会自动触发商品明细的重新计算
        """
        # 验证发货单是否存在
        shipment = ShipmentOrder.query.get(shipment_id)
        if not shipment:
            raise BusinessError('发货单不存在', code=404)
        
        # 验证发货单状态（只有草稿状态才能添加采购明细）
        if shipment.status != 'draft':
            raise BusinessError('只有草稿状态的发货单才能添加采购明细', code=400)
        
        # 获取商品变体
        # 如果没有提供product_variant_id，尝试通过SKU查找
        product_variant = None
        if 'product_variant_id' in data and data['product_variant_id']:
            product_variant = ProductVariant.query.get(data['product_variant_id'])
        elif 'sku' in data and data['sku']:
            product_variant = ProductVariant.query.filter_by(sku=data['sku']).first()
            if product_variant:
                data['product_variant_id'] = product_variant.id
        
        if not product_variant:
            raise BusinessError('商品变体不存在，请检查SKU是否正确', code=404)
        
        # 如果没有提供SKU，使用商品变体的SKU
        if 'sku' not in data or not data['sku']:
            data['sku'] = product_variant.sku
        
        # 如果没有提供商品名称，使用商品变体的名称
        if 'product_name' not in data or not data['product_name']:
            data['product_name'] = product_variant.product.name if product_variant.product else data['sku']
        
        # 计算采购总价
        data['purchase_total_price'] = data['quantity'] * data['purchase_unit_price']
        
        # 创建采购明细
        purchase_item = ShipmentPurchaseItem(
            shipment_order_id=shipment_id,
            created_by=get_jwt_identity(),
            **data
        )
        
        db.session.add(purchase_item)
        db.session.flush()
        
        # 自动更新商品明细
        ShipmentPurchaseItemService._update_item_for_sku(shipment_id, purchase_item.sku)
        
        db.session.commit()
        
        return purchase_item
    
    @staticmethod
    def update_purchase_item(purchase_item_id: int, data: dict) -> ShipmentPurchaseItem:
        """
        更新采购明细
        
        更新后会自动触发商品明细的重新计算
        """
        purchase_item = ShipmentPurchaseItem.query.get(purchase_item_id)
        if not purchase_item:
            raise BusinessError('采购明细不存在', code=404)
        
        # 验证发货单状态
        shipment = purchase_item.shipment_order
        if shipment.status != 'draft':
            raise BusinessError('只有草稿状态的发货单才能修改采购明细', code=400)
        
        # 更新字段
        for key, value in data.items():
            if hasattr(purchase_item, key):
                setattr(purchase_item, key, value)
        
        # 重新计算采购总价
        if 'quantity' in data or 'purchase_unit_price' in data:
            purchase_item.purchase_total_price = purchase_item.quantity * purchase_item.purchase_unit_price
        
        db.session.flush()
        
        # 自动更新商品明细
        ShipmentPurchaseItemService._update_item_for_sku(
            purchase_item.shipment_order_id, 
            purchase_item.sku
        )
        
        db.session.commit()
        
        return purchase_item
    
    @staticmethod
    def delete_purchase_item(purchase_item_id: int) -> None:
        """
        删除采购明细
        
        删除后会自动触发商品明细的重新计算
        """
        purchase_item = ShipmentPurchaseItem.query.get(purchase_item_id)
        if not purchase_item:
            raise BusinessError('采购明细不存在', code=404)
        
        # 验证发货单状态
        shipment = purchase_item.shipment_order
        if shipment.status != 'draft':
            raise BusinessError('只有草稿状态的发货单才能删除采购明细', code=400)
        
        shipment_id = purchase_item.shipment_order_id
        sku = purchase_item.sku
        
        db.session.delete(purchase_item)
        db.session.flush()
        
        # 自动更新商品明细
        ShipmentPurchaseItemService._update_item_for_sku(shipment_id, sku)
        
        db.session.commit()
    
    @staticmethod
    def get_purchase_items(shipment_id: int, group_by: str = None):
        """
        获取采购明细列表
        
        Args:
            shipment_id: 发货单ID
            group_by: 分组方式 ('supplier', 'purchase_order', 'sku', None)
        
        Returns:
            采购明细对象列表或分组数据（dict）
        """
        query = ShipmentPurchaseItem.query.filter_by(shipment_order_id=shipment_id)
        
        if group_by == 'supplier':
            # 按供应商分组，返回dict
            return ShipmentPurchaseItemService._group_by_supplier(query.all())
        elif group_by == 'purchase_order':
            # 按采购订单分组，返回dict
            return ShipmentPurchaseItemService._group_by_purchase_order(query.all())
        elif group_by == 'sku':
            # 按SKU分组，返回dict
            return ShipmentPurchaseItemService._group_by_sku(query.all())
        else:
            # 不分组，返回对象列表（让Schema自己序列化）
            return query.all()
    
    @staticmethod
    def recalculate_all_items(shipment_id: int) -> None:
        """
        重新计算整个发货单的商品明细（全量重算）
        
        场景：数据修复、批量导入后
        """
        # 获取所有采购明细的SKU列表
        skus = db.session.query(
            ShipmentPurchaseItem.sku
        ).filter_by(
            shipment_order_id=shipment_id
        ).distinct().all()
        
        # 清空现有商品明细
        ShipmentOrderItem.query.filter_by(
            shipment_id=shipment_id
        ).delete()
        
        # 逐个SKU重新计算
        for (sku,) in skus:
            ShipmentPurchaseItemService._update_item_for_sku(shipment_id, sku)
        
        db.session.commit()
    
    @staticmethod
    def _update_item_for_sku(shipment_id: int, sku: str) -> None:
        """
        重新计算单个SKU的商品明细（核心算法）
        
        算法逻辑：
        1. 查询该SKU的所有采购明细
        2. 汇总数量
        3. 计算加权平均单价（已废弃，商品明细不再存储价格）
        4. 确定主供应商（数量最多的）
        5. 更新或创建商品明细
        """
        # 1. 查询该SKU的所有采购明细
        purchase_items = ShipmentPurchaseItem.query.filter_by(
            shipment_order_id=shipment_id,
            sku=sku
        ).all()
        
        if not purchase_items:
            # 如果没有采购明细了，删除商品明细
            ShipmentOrderItem.query.filter_by(
                shipment_id=shipment_id,
                sku=sku
            ).delete()
            return
        
        # 2. 汇总数据
        total_quantity = sum(item.quantity for item in purchase_items)
        
        # 3. 确定主供应商（数量最多的）和供应商名称
        supplier_quantities = Counter()
        supplier_names = {}
        for item in purchase_items:
            if item.supplier_id:
                supplier_quantities[item.supplier_id] += item.quantity
                supplier_names[item.supplier_id] = item.supplier_name
        
        main_supplier_id = supplier_quantities.most_common(1)[0][0] if supplier_quantities else None
        main_supplier_name = supplier_names.get(main_supplier_id) if main_supplier_id else None
        
        # 4. 获取第一个采购明细的商品信息
        first_item = purchase_items[0]
        product_variant = first_item.product_variant
        
        # 5. 更新或创建商品明细
        shipment_item = ShipmentOrderItem.query.filter_by(
            shipment_id=shipment_id,
            sku=sku
        ).first()
        
        if shipment_item:
            # 更新现有商品明细
            shipment_item.quantity = total_quantity
            shipment_item.supplier_id = main_supplier_id
            shipment_item.supplier_name = main_supplier_name
            shipment_item.product_name = first_item.product_name
            shipment_item.unit = first_item.unit
            # 价格字段不再更新，保持为None或原值
        else:
            # 创建新的商品明细
            shipment_item = ShipmentOrderItem(
                shipment_id=shipment_id,
                product_id=product_variant.product_id if product_variant else None,
                sku=sku,
                product_name=first_item.product_name,
                quantity=total_quantity,
                unit=first_item.unit,
                supplier_id=main_supplier_id,
                supplier_name=main_supplier_name,
                # 价格字段设置为None（不再使用）
                unit_price=None,
                total_price=None,
                tax_rate=None,
                tax_amount=None,
                unit_price_with_tax=None,
                total_price_with_tax=None,
            )
            db.session.add(shipment_item)
    
    @staticmethod
    def _group_by_supplier(purchase_items: List[ShipmentPurchaseItem]) -> List[Dict]:
        """按供应商分组"""
        supplier_groups = {}
        
        for item in purchase_items:
            supplier_key = item.supplier_id or 'unknown'
            supplier_name = item.supplier_name or '未指定供应商'
            
            if supplier_key not in supplier_groups:
                supplier_groups[supplier_key] = {
                    'supplier_id': item.supplier_id,
                    'supplier_name': supplier_name,
                    'items': [],
                    'total_quantity': 0,
                    'total_amount': Decimal('0')
                }
            
            supplier_groups[supplier_key]['items'].append(item.to_dict())
            supplier_groups[supplier_key]['total_quantity'] += item.quantity
            supplier_groups[supplier_key]['total_amount'] += item.purchase_total_price
        
        return list(supplier_groups.values())
    
    @staticmethod
    def _group_by_purchase_order(purchase_items: List[ShipmentPurchaseItem]) -> List[Dict]:
        """按采购订单分组"""
        po_groups = {}
        
        for item in purchase_items:
            po_key = item.purchase_order_no or 'unknown'
            
            if po_key not in po_groups:
                po_groups[po_key] = {
                    'purchase_order_id': item.purchase_order_id,
                    'purchase_order_no': item.purchase_order_no or '未关联采购单',
                    'supplier_name': item.supplier_name,
                    'items': [],
                    'total_quantity': 0,
                    'total_amount': Decimal('0')
                }
            
            po_groups[po_key]['items'].append(item.to_dict())
            po_groups[po_key]['total_quantity'] += item.quantity
            po_groups[po_key]['total_amount'] += item.purchase_total_price
        
        return list(po_groups.values())
    
    @staticmethod
    def _group_by_sku(purchase_items: List[ShipmentPurchaseItem]) -> List[Dict]:
        """按SKU分组"""
        sku_groups = {}
        
        for item in purchase_items:
            if item.sku not in sku_groups:
                sku_groups[item.sku] = {
                    'sku': item.sku,
                    'product_name': item.product_name,
                    'items': [],
                    'total_quantity': 0,
                    'total_amount': Decimal('0')
                }
            
            sku_groups[item.sku]['items'].append(item.to_dict())
            sku_groups[item.sku]['total_quantity'] += item.quantity
            sku_groups[item.sku]['total_amount'] += item.purchase_total_price
        
        return list(sku_groups.values())
    
    @staticmethod
    def validate_shipment_consistency(shipment_id: int) -> Dict:
        """
        验证发货单的数据一致性
        
        检查项：
        1. 采购明细数量 vs 商品明细数量
        2. 必须有采购明细
        3. 必须有商品明细
        
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 检查采购明细
        purchase_count = ShipmentPurchaseItem.query.filter_by(
            shipment_order_id=shipment_id
        ).count()
        
        if purchase_count == 0:
            errors.append('发货单必须包含至少一条采购明细')
        
        # 检查商品明细
        item_count = ShipmentOrderItem.query.filter_by(
            shipment_id=shipment_id
        ).count()
        
        if item_count == 0:
            errors.append('商品明细未生成，请先添加采购明细')
        
        # 检查数量一致性
        for item in ShipmentOrderItem.query.filter_by(shipment_id=shipment_id).all():
            purchase_total = db.session.query(
                func.sum(ShipmentPurchaseItem.quantity)
            ).filter_by(
                shipment_order_id=shipment_id,
                sku=item.sku
            ).scalar() or 0
            
            if purchase_total != item.quantity:
                errors.append(
                    f'SKU {item.sku} 的数量不一致：'
                    f'商品明细={item.quantity}，'
                    f'采购明细合计={purchase_total}'
                )
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

