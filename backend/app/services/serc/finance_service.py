from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.supply import ScmDeliveryContract, ScmDeliveryContractItem
from app.models.serc.finance import FinSupplyContract, FinSupplyContractItem, FinPurchaseSOA, FinPurchaseSOADetail, FinPaymentPoolOld, SysPaymentTerm
from app.models.purchase.supplier import SysSupplier
from app.models.product import Product, SysTaxCategory
from app.errors import BusinessError

class FinanceService:
    def preview_supply_contract_from_l1(self, l1_contract_id: int) -> Dict:
        """
        预览 L1.5 供货合同 (不落库)
        用于前端展示聚合结果，供财务确认
        """
        l1_contract = db.session.get(ScmDeliveryContract, l1_contract_id)
        if not l1_contract:
            raise BusinessError("Delivery contract not found")
        
        # 1. 获取供应商税务信息
        supplier = db.session.get(SysSupplier, l1_contract.supplier_id)
        if not supplier:
            raise BusinessError("Supplier not found")
            
        # 2. 聚合明细
        aggregated_items = self._aggregate_items(l1_contract.items, supplier)
        
        # 3. 计算总额
        total_amount = sum(item['amount'] for item in aggregated_items)
        # 校验平衡性 (允许 0.05 元以内的尾差)
        diff = total_amount - l1_contract.total_amount
        is_balanced = abs(diff) <= Decimal('0.05')
        
        return {
            "data": {
                "l1_contract_id": l1_contract.id,
                "contract_no": l1_contract.contract_no,
                "supplier_name": supplier.name,
                "l1_total_amount": l1_contract.total_amount,
                "preview_total_amount": total_amount,
                "diff": diff,
                "is_balanced": is_balanced,
                "items": aggregated_items,
                "warnings": self._collect_warnings(aggregated_items)
            }
        }

    def create_supply_contract_from_l1(self, l1_contract_id: int, confirmed_items: List[Dict]) -> FinSupplyContract:
        """
        正式创建 L1.5 供货合同 (落库)
        """
        l1_contract = db.session.get(ScmDeliveryContract, l1_contract_id)
        if not l1_contract:
            raise BusinessError("Delivery contract not found")
            
        # Check uniqueness
        existing = db.session.query(FinSupplyContract).filter_by(l1_contract_id=l1_contract_id).first()
        if existing:
            raise BusinessError("Supply contract already exists for this delivery")
            
        # 1. 校验总额
        current_total = sum(Decimal(str(item['amount'])) for item in confirmed_items)
        if abs(current_total - l1_contract.total_amount) > Decimal('0.05'):
             raise BusinessError(f"Total amount mismatch: L1={l1_contract.total_amount}, L1.5={current_total}")
             
        # 2. 创建主表
        supply_contract = FinSupplyContract(
            l1_contract_id=l1_contract.id,
            contract_no=l1_contract.contract_no,
            supplier_id=l1_contract.supplier_id,
            total_amount=l1_contract.total_amount,
            currency=l1_contract.currency,
            status='draft'
        )
        db.session.add(supply_contract)
        db.session.flush()
        
        # 3. 创建明细
        for item_data in confirmed_items:
            item = FinSupplyContractItem(
                supply_contract_id=supply_contract.id,
                invoice_name=item_data['invoice_name'],
                invoice_unit=item_data.get('invoice_unit', 'PCS'),
                specs=item_data.get('specs'),
                quantity=Decimal(str(item_data['quantity'])),
                price_unit=Decimal(str(item_data['price_unit'])),
                amount=Decimal(str(item_data['amount'])),
                tax_rate=Decimal(str(item_data['tax_rate'])),
                tax_code=item_data.get('tax_code', '')
            )
            db.session.add(item)
            
        return supply_contract

    def generate_soa(self, l1_ids: List[int]) -> FinPurchaseSOA:
        """
        生成 L2 结算单 (SOA)
        将多个 L1 交付单（属于同一供应商）合并生成一张 SOA
        """
        if not l1_ids:
             raise BusinessError("No contracts selected")

        contracts = db.session.query(ScmDeliveryContract).filter(ScmDeliveryContract.id.in_(l1_ids)).all()
        if len(contracts) != len(l1_ids):
             raise BusinessError("Some contracts not found")

        # Check Same Supplier
        supplier_id = contracts[0].supplier_id
        if any(c.supplier_id != supplier_id for c in contracts):
             raise BusinessError("Contracts must belong to the same supplier")

        # Check Uniqueness (Avoid adding same contract to multiple SOAs)
        # Assuming one-to-one mapping in Detail.
        # Check if already in detail
        existing_details = db.session.query(FinPurchaseSOADetail.l1_contract_id)\
            .filter(FinPurchaseSOADetail.l1_contract_id.in_(l1_ids)).all()
        if existing_details:
             raise BusinessError(f"Contracts {existing_details} already in SOA")

        # Create SOA Header
        total_amount = sum(c.total_amount for c in contracts)
        soa_no = f"SOA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{supplier_id}"
        
        soa = FinPurchaseSOA(
            soa_no=soa_no,
            supplier_id=supplier_id,
            total_payable=total_amount,
            currency=contracts[0].currency, # Assume same currency
            status='draft'
        )
        db.session.add(soa)
        db.session.flush()

        # Create Details
        for c in contracts:
            detail = FinPurchaseSOADetail(
                soa_id=soa.id,
                l1_contract_id=c.id,
                amount=c.total_amount
            )
            db.session.add(detail)
            
            # Update FinSupplyContract status if exists
            fin_contract = db.session.query(FinSupplyContract).filter_by(l1_contract_id=c.id).first()
            if fin_contract:
                fin_contract.status = 'soa_generated'
                fin_contract.reconciled_amount = fin_contract.total_amount # Full reconcile

        db.session.commit()
        return soa

    def confirm_soa(self, soa_id: int) -> FinPurchaseSOA:
        """
        确认 SOA (供应商对账完成)
        """
        soa = db.session.get(FinPurchaseSOA, soa_id)
        if not soa:
            raise BusinessError("SOA not found")
        
        if soa.status != 'draft':
            raise BusinessError(f"Cannot confirm SOA in status {soa.status}")
            
        soa.status = 'confirmed'
        db.session.commit()
        return soa

    def approve_soa(self, soa_id: int) -> FinPurchaseSOA:
        """
        批准 SOA 并生成付款计划 (L3)
        """
        soa = db.session.get(FinPurchaseSOA, soa_id)
        if not soa:
            raise BusinessError("SOA not found")
        
        if soa.status != 'confirmed':
            raise BusinessError(f"Cannot approve SOA in status {soa.status}")
            
        # 1. Update Status
        soa.status = 'approved'
        
        # 2. Get Supplier Payment Terms
        supplier = soa.supplier
        term = supplier.payment_term if supplier else None
        
        # 3. Calculate Due Date
        due_date = datetime.now().date()
        if term:
            # Simple logic: baseline + offset
            # baseline defaults to event_date (today) for simplicity unless we have more dates in SOA
            due_date = due_date + timedelta(days=term.days_offset)
            
        # 4. Generate Payment Pool Entry
        pool_item = FinPaymentPoolOld(
            soa_id=soa.id,
            amount=soa.total_payable,
            currency=soa.currency,
            due_date=due_date,
            status='pending_approval',
            priority=50 # Default priority
        )
        db.session.add(pool_item)
        
        db.session.commit()
        return soa

    def _aggregate_items(self, l1_items: List[ScmDeliveryContractItem], supplier: SysSupplier) -> List[Dict]:
        """
        核心聚合逻辑
        Key = (invoice_name, invoice_unit, tax_rate, price_unit)
        """
        # 1. 预处理
        processed_items = []
        for item in l1_items:
            product = item.product or db.session.get(Product, item.product_id)
            
            # A. 确定开票名称 (Priority: Product.declared_name > Product.name)
            invoice_name = product.declared_name if product.declared_name else product.name
            
            # B. 确定税率 (Priority: Supplier.default > TaxCategory.ref > 0.13)
            if supplier.default_vat_rate is not None:
                tax_rate = supplier.default_vat_rate
            elif product.tax_category and product.tax_category.reference_rate:
                tax_rate = product.tax_category.reference_rate
            else:
                tax_rate = Decimal('0.13') # System default fallback
                
            # C. 确定税收编码
            tax_code = product.tax_category.code if product.tax_category else ""
            
            processed_items.append({
                'invoice_name': invoice_name,
                'invoice_unit': product.declared_unit or 'PCS', # Default unit
                'tax_rate': tax_rate,
                'tax_code': tax_code,
                'quantity': item.confirmed_qty,
                'amount': item.total_price, # Use line total amount to avoid precision loss first
                # Store original for debugging
                'original_sku': product.sku
            })
            
        # 2. 分组聚合
        # Group by: (invoice_name, tax_rate, tax_code)
        # Note: We do NOT group by price initially, we calculate weighted average price later
        # OR: We can group by price if we want strict price separation. 
        # Usually for finance, weighted average price is acceptable for same product name.
        
        groups = defaultdict(lambda: {'quantity': Decimal(0), 'amount': Decimal(0), 'skus': set()})
        
        for p in processed_items:
            # Key definition
            key = (p['invoice_name'], p['invoice_unit'], p['tax_rate'], p['tax_code'])
            
            groups[key]['quantity'] += p['quantity']
            groups[key]['amount'] += p['amount']
            groups[key]['skus'].add(p['original_sku'])
            
        # 3. 格式化输出
        results = []
        for key, val in groups.items():
            invoice_name, invoice_unit, tax_rate, tax_code = key
            qty = val['quantity']
            amt = val['amount']
            
            # Back-calculate unit price
            price_unit = amt / qty if qty != 0 else Decimal(0)
            
            results.append({
                'invoice_name': invoice_name,
                'invoice_unit': invoice_unit,
                'specs': '', # Can be used to list skus or "Batch"
                'quantity': qty,
                'price_unit': round(price_unit, 4), # 4 decimal places for unit price
                'amount': amt,
                'tax_rate': tax_rate,
                'tax_code': tax_code,
                'skus': list(val['skus'])
            })
            
        return results

    def _collect_warnings(self, items: List[Dict]) -> List[str]:
        warnings = []
        for item in items:
            if not item['tax_code']:
                warnings.append(f"品名 '{item['invoice_name']}' 缺失税收分类编码")
        return warnings

finance_service = FinanceService()
