from typing import List, Dict, Any
from decimal import Decimal
from sqlalchemy import func
from app.extensions import db
from app.models.serc.tax import TaxInvoiceItem, TaxInvoice, TaxRefundMatch
from app.models.customs import CustomsDeclaration, CustomsDeclarationItem
from app.models.serc.enums import TaxInvoiceStatus, CustomsStatus
from app.models.product import Product

class TaxRefundService:
    def match_declaration(self, declaration_id: int) -> Dict[str, Any]:
        """
        尝试为报关单匹配发票 (Item-Level Fitting Algorithm)
        规则：同一个报关单项号必须一次性匹配满，不可拆分申报。
        """
        decl = db.session.get(CustomsDeclaration, declaration_id)
        if not decl:
            return {"success": False, "message": "Declaration not found"}
            
        results = []
        all_matched = True
        
        # 预加载商品信息
        for item in decl.items:
            product = item.product
            if not product:
                results.append({
                    "item_id": item.id, 
                    "status": "fail", 
                    "reason": "商品关联缺失"
                })
                all_matched = False
                continue
                
            declared_name = product.declared_name or product.name
            needed_qty = item.qty
            
            # 查找该商品名称下的所有发票明细 (按时间正序)
            # 注意：不限制 status='free'，因为可能存在部分使用的发票
            # 但要排除已经 status='locked' (已归档) 的发票? 
            # 假设只要还有余额就可以用。
            candidates = db.session.query(TaxInvoiceItem).join(TaxInvoice).filter(
                TaxInvoiceItem.name == declared_name,
                TaxInvoice.status != TaxInvoiceStatus.LOCKED.value 
            ).order_by(TaxInvoice.created_at.asc()).all()
            
            selected_plan = []
            current_collected_qty = Decimal(0)
            
            # 尝试凑数
            for inv_item in candidates:
                if current_collected_qty >= needed_qty:
                    break
                    
                # 计算该发票项的剩余可用数量
                # used = sum(matches)
                used_qty = db.session.query(func.sum(TaxRefundMatch.matched_qty))\
                    .filter(TaxRefundMatch.invoice_item_id == inv_item.id).scalar() or Decimal(0)
                
                available = inv_item.qty - used_qty
                
                if available <= Decimal('0.0001'):
                    continue
                    
                # 需要多少
                remaining_needed = needed_qty - current_collected_qty
                
                # 取多少
                take = min(available, remaining_needed)
                
                selected_plan.append({
                    "invoice_item_id": inv_item.id,
                    "invoice_no": inv_item.invoice.invoice_no,
                    "take_qty": take
                })
                current_collected_qty += take
                
            # 判定该项是否匹配成功
            if current_collected_qty >= needed_qty:
                # 允许微小误差? 报关单要求数量严格一致。
                # 实际上如果发票有富余是允许的，但必须涵盖报关数量。
                results.append({
                    "item_id": item.id,
                    "product_name": declared_name,
                    "status": "success",
                    "plan": selected_plan
                })
            else:
                all_matched = False
                results.append({
                    "item_id": item.id,
                    "product_name": declared_name,
                    "status": "fail",
                    "reason": f"发票库存不足: 需 {needed_qty}, 仅有 {current_collected_qty}"
                })
                
        return {
            "success": all_matched,
            "results": results
        }

    def confirm_match(self, declaration_id: int) -> bool:
        """
        确认匹配结果并持久化
        此方法会重新运行匹配算法以确保并发安全性
        """
        match_result = self.match_declaration(declaration_id)
        if not match_result.get('success'):
            return False
        
        results = match_result['results']
        
        try:
            for res in results:
                customs_item_id = res['item_id']
                for plan_item in res['plan']:
                    invoice_item_id = plan_item['invoice_item_id']
                    take_qty = Decimal(str(plan_item['take_qty']))
                    
                    # 1. Create Match Record
                    match = TaxRefundMatch(
                        customs_item_id=customs_item_id,
                        invoice_item_id=invoice_item_id,
                        matched_qty=take_qty
                    )
                    db.session.add(match)
                    
                    # 2. Check and Update Invoice Status
                    self._update_invoice_status(invoice_item_id)
            
            # 3. Update Declaration Status
            decl = db.session.get(CustomsDeclaration, declaration_id)
            decl.status = CustomsStatus.PRE_DECLARED.value # 预申报状态
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def cancel_match(self, declaration_id: int) -> bool:
        """
        解除匹配 (释放发票)
        用于报关单驳回、撤销或修正场景
        """
        decl = db.session.get(CustomsDeclaration, declaration_id)
        if not decl:
            return False
            
        # 只能撤销预申报状态或正式申报状态(需特批)的单据
        # 暂定: 只有 PRE_DECLARED 可撤销
        if decl.status != CustomsStatus.PRE_DECLARED.value:
            return False
            
        try:
            # 1. 查找所有关联的匹配记录
            matches = db.session.query(TaxRefundMatch).join(CustomsDeclarationItem)\
                .filter(CustomsDeclarationItem.declaration_id == declaration_id).all()
            
            affected_invoice_item_ids = set()
            
            # 2. 删除匹配记录
            for match in matches:
                affected_invoice_item_ids.add(match.invoice_item_id)
                db.session.delete(match)
            
            # 3. 重新计算发票状态
            # Flush first to ensure deletions are visible to query in _update_invoice_status
            db.session.flush() 
            
            for inv_item_id in affected_invoice_item_ids:
                self._update_invoice_status(inv_item_id)
                
            # 4. 回滚报关单状态
            decl.status = CustomsStatus.DRAFT.value
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e

    def _update_invoice_status(self, invoice_item_id: int):
        """
        更新发票项及发票主表的状态
        逻辑: 如果发票项用完了，检查主表所有项是否用完
        """
        inv_item = db.session.get(TaxInvoiceItem, invoice_item_id)
        if not inv_item:
            return
            
        # Calculate used quantity for this item
        used_qty = db.session.query(func.sum(TaxRefundMatch.matched_qty))\
            .filter(TaxRefundMatch.invoice_item_id == invoice_item_id).scalar() or Decimal(0)
            
        # Check if item is fully used
        # Use a small epsilon for float comparison
        # item_fully_used = (inv_item.qty - used_qty) <= Decimal('0.0001')
        
        # We don't have status on Item level, only on Header level
        # Check all items in this invoice
        invoice = inv_item.invoice
        all_items_used = True
        any_item_used = False
        
        for item in invoice.items:
            # We need to query used_qty for each item
            i_used = db.session.query(func.sum(TaxRefundMatch.matched_qty))\
                .filter(TaxRefundMatch.invoice_item_id == item.id).scalar() or Decimal(0)
            
            if i_used > Decimal('0.0001'):
                any_item_used = True
                
            if (item.qty - i_used) > Decimal('0.0001'):
                all_items_used = False
                # If we found an unused part, we know it's not LOCKED.
                # But we still need to check if ANY used to decide between FREE and RESERVED.
        
        if all_items_used:
            invoice.status = TaxInvoiceStatus.LOCKED.value # Fully used
        elif any_item_used:
            invoice.status = TaxInvoiceStatus.RESERVED.value # Partially used
        else:
            invoice.status = TaxInvoiceStatus.FREE.value # Not used at all

tax_refund_service = TaxRefundService()
