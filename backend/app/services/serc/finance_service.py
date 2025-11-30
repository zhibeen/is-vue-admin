from typing import List
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select
from app.extensions import db
from app.models.serc.finance import (
    FinPurchaseSOA, FinPurchaseSOADetail, 
    FinPaymentPool, FinPaymentRequest, FinPaymentReconcile
)
from app.models.supply import ScmDeliveryContract
from app.models.purchase.supplier import SysSupplier
from app.models.serc.enums import (
    ContractStatus, SettlementStatus, InvoiceStatus, 
    PaymentPoolStatus, PaymentType
)
from app.services.serc.common import generate_seq_no

class FinanceService:
    def generate_soa(self, l1_ids: List[int]) -> FinPurchaseSOA:
        """
        根据 L1 合同生成 L2 结算单 (SOA)
        逻辑:
        1. 校验: 所有 L1 必须同供应商、且状态为 PENDING
        2. 锁定: 更新 L1 状态为 SETTLING
        3. 创建 SOA 主表
        4. 创建 SOA Detail 明细 (建立资金追踪桥梁)
        5. 自动入池 (简化起见，默认全额入池为 '尾款')
        """
        # 1. 获取所有 L1 合同
        contracts = db.session.scalars(
            select(ScmDeliveryContract).where(ScmDeliveryContract.id.in_(l1_ids))
        ).all()

        if len(contracts) != len(l1_ids):
            raise ValueError("部分合同ID无效")
        
        if not contracts:
            raise ValueError("未选择任何合同")

        # 校验一致性
        first_supplier = contracts[0].supplier_id
        for c in contracts:
            if c.supplier_id != first_supplier:
                raise ValueError("必须选择同一供应商的合同生成结算单")
            if c.status != ContractStatus.PENDING.value:
                raise ValueError(f"合同 {c.contract_no} 不是待结算状态")

        # 2. 准备数据
        total_amount = sum(c.total_amount for c in contracts)
        soa_no = generate_seq_no("SOA")

        # 3. 创建 SOA 主表
        soa = FinPurchaseSOA(
            soa_no=soa_no,
            supplier_id=first_supplier,
            total_payable=total_amount,
            paid_amount=Decimal("0.00"),
            invoiced_amount=Decimal("0.00"),
            payment_status=SettlementStatus.UNPAID.value,
            invoice_status=InvoiceStatus.NONE.value
        )
        db.session.add(soa)
        db.session.flush() # 获取 ID

        # 4. 创建 Detail 并锁定 L1
        for c in contracts:
            # 锁定 L1
            c.status = ContractStatus.SETTLING.value
            
            # 创建 Detail
            detail = FinPurchaseSOADetail(
                soa_id=soa.id,
                l1_contract_id=c.id,
                amount=c.total_amount,
                allocated_payment=Decimal("0.00")
            )
            db.session.add(detail)

        # 5. 自动推送到付款池 (默认策略: 全额作为尾款)
        # 实际业务中可能由用户手动触发，这里为了闭环直接生成
        pool_item = FinPaymentPool(
            soa_id=soa.id,
            amount=total_amount,
            type=PaymentType.BALANCE.value,
            priority=0,
            status=PaymentPoolStatus.PENDING_APPROVAL.value
        )
        db.session.add(pool_item)

        db.session.commit()
        return soa

    def execute_payment(self, pool_item_ids: List[int], bank_account: str) -> FinPaymentRequest:
        """
        执行付款 (生成 L3)
        逻辑:
        1. 汇总池中条目金额
        2. 生成 L3 付款单
        3. 更新 Pool Item 状态 -> PAID
        4. 回写 L2 SOA 状态 (paid_amount, payment_status)
        5. (高级) 回写 L2 Detail 的 allocated_payment
        """
        pool_items = db.session.scalars(
            select(FinPaymentPool).where(FinPaymentPool.id.in_(pool_item_ids))
        ).all()

        if not pool_items:
            raise ValueError("未选择付款项")

        # 校验状态
        for item in pool_items:
            if item.status == PaymentPoolStatus.PAID.value:
                raise ValueError(f"条目 {item.id} 已支付，不可重复支付")

        # 1. 汇总金额
        total_pay = sum(item.amount for item in pool_items)
        request_no = generate_seq_no("PAY")

        # 2. 生成 L3
        pay_req = FinPaymentRequest(
            request_no=request_no,
            total_pay_amount=total_pay,
            bank_account=bank_account
        )
        db.session.add(pay_req)
        
        # 3. 处理每个池中条目 & 回写 SOA
        # 注意: 一个 L3 可能对应多个 Pool Item，每个 Pool Item 对应一个 SOA
        soa_updates = {}  # {soa_id: pay_amount}

        for item in pool_items:
            item.status = PaymentPoolStatus.PAID.value
            
            # 记录每个 SOA 此次付了多少钱
            if item.soa_id not in soa_updates:
                soa_updates[item.soa_id] = Decimal("0.00")
            soa_updates[item.soa_id] += item.amount

        db.session.flush()

        # 4. 回写 SOA 状态
        for soa_id, amount_paid in soa_updates.items():
            soa = db.session.get(FinPurchaseSOA, soa_id)
            if soa:
                soa.paid_amount += amount_paid
                
                # 更新状态
                if soa.paid_amount >= soa.total_payable:
                    soa.payment_status = SettlementStatus.PAID.value
                elif soa.paid_amount > 0:
                    soa.payment_status = SettlementStatus.PARTIAL.value
                
                # (高级) 资金穿透: 将付款金额分摊到 L2 Detail 上
                # 简化策略: 按比例分摊，或者按顺序填坑。这里采用按比例。
                if soa.total_payable > 0:
                    ratio = amount_paid / soa.total_payable
                    for detail in soa.details:
                        # 分摊逻辑: 本次付款 * (Detail占比)
                        # 注意: 这样多次分摊可能会有精度误差，实际工程需处理尾差
                        detail_pay = detail.amount * ratio
                        detail.allocated_payment += detail_pay
                        
                        # 如果 SOA 结清了，强制 Detail 也结清 (避免尾差)
                        if soa.payment_status == SettlementStatus.PAID.value:
                            detail.allocated_payment = detail.amount

        db.session.commit()
        return pay_req

finance_service = FinanceService()

