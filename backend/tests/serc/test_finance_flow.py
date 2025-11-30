import pytest
from decimal import Decimal
from app.services.serc.finance_service import finance_service
from app.models.serc.finance import FinPurchaseSOA, FinPaymentPool, FinPurchaseSOADetail
from app.models.serc.enums import SettlementStatus, ContractStatus, PaymentPoolStatus, PaymentType
from tests.factories import (
    SysSupplierFactory, ProductFactory, 
    ScmDeliveryContractFactory, ScmDeliveryItemFactory
)

@pytest.mark.usefixtures("client") # 确保 app 上下文
class TestFinanceFlow:
    
    def test_full_payment_flow(self, db_session):
        """
        测试完整资金流转: L1 -> L2 -> Pool -> Payment -> L2 Update
        """
        # 1. 准备数据
        supplier = SysSupplierFactory()
        product = ProductFactory()
        db_session.commit()

        # 创建两个 L1 合同
        # Contract A: 1000元
        c1 = ScmDeliveryContractFactory(supplier=supplier, total_amount=1000)
        ScmDeliveryItemFactory(contract=c1, product=product, confirmed_qty=10, unit_price=100, total_price=1000)
        
        # Contract B: 2000元
        c2 = ScmDeliveryContractFactory(supplier=supplier, total_amount=2000)
        ScmDeliveryItemFactory(contract=c2, product=product, confirmed_qty=20, unit_price=100, total_price=2000)
        
        db_session.commit()

        # 2. 生成 L2 (SOA)
        soa = finance_service.generate_soa([c1.id, c2.id])
        
        # 断言: L2 生成正确
        assert soa is not None
        assert soa.total_payable == 3000
        assert soa.paid_amount == 0
        assert soa.payment_status == SettlementStatus.UNPAID.value
        
        # 断言: L1 状态锁定
        assert c1.status == ContractStatus.SETTLING.value
        assert c2.status == ContractStatus.SETTLING.value
        
        # 断言: Detail 生成正确
        details = db_session.query(FinPurchaseSOADetail).filter_by(soa_id=soa.id).all()
        assert len(details) == 2
        assert details[0].allocated_payment == 0
        
        # 断言: 自动入池
        pool_items = db_session.query(FinPaymentPool).filter_by(soa_id=soa.id).all()
        assert len(pool_items) == 1
        pool_item = pool_items[0]
        assert pool_item.amount == 3000
        assert pool_item.status == PaymentPoolStatus.PENDING_APPROVAL.value

        # 3. 执行部分付款 (付 1500)
        # 修改 Pool Item 金额模拟“先付一半”
        pool_item.amount = 1500
        db_session.commit()
        
        pay_req = finance_service.execute_payment([pool_item.id], "BANK-001")
        
        # 4. 断言: 付款后状态回写
        db_session.refresh(soa)
        assert soa.paid_amount == 1500
        assert soa.payment_status == SettlementStatus.PARTIAL.value
        
        # 断言: Detail 分摊 (50% 比例)
        # C1 (1000) 应该分摊到 500
        # C2 (2000) 应该分摊到 1000
        detail_c1 = next(d for d in soa.details if d.l1_contract_id == c1.id)
        detail_c2 = next(d for d in soa.details if d.l1_contract_id == c2.id)
        
        assert detail_c1.allocated_payment == 500
        assert detail_c2.allocated_payment == 1000
        
        # 5. 再次付款 (付剩余 1500)
        # 需要手动再造一个 Pool Item (模拟尾款申请)
        pool_item_2 = FinPaymentPool(
            soa_id=soa.id, 
            amount=1500, 
            type=PaymentType.BALANCE.value,
            status=PaymentPoolStatus.PENDING_APPROVAL.value
        )
        db_session.add(pool_item_2)
        db_session.commit()
        
        finance_service.execute_payment([pool_item_2.id], "BANK-001")
        
        # 6. 断言: 全额结清
        db_session.refresh(soa)
        assert soa.paid_amount == 3000
        assert soa.payment_status == SettlementStatus.PAID.value
        
        # 强制结清检查 (Detail 必须全满)
        db_session.refresh(detail_c1)
        assert detail_c1.allocated_payment == 1000

