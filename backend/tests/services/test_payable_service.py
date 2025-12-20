"""
财务应付单服务层测试
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from app.services.serc.payable_service import PayableService
from app.models.serc.payable import FinPayable, PayableStatus, FinPaymentPool, PaymentPoolStatus
from app.errors import BusinessError
from tests.factories import (
    FinPayableFactory,
    FinPaymentPoolFactory,
    LogisticsProviderFactory,
    LogisticsStatementFactory,
    UserFactory
)


class TestPayableService:
    """测试财务应付单服务"""
    
    def test_generate_payable_no(self, app):
        """测试生成应付单号"""
        with app.app_context():
            payable_no = PayableService.generate_payable_no()
            assert payable_no.startswith('AP')
            assert len(payable_no) == 14  # AP(2) + YYYYMMDD(8) + 4位数字(4)
    
    def test_create_payable(self, app):
        """测试创建应付单"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            user = UserFactory()
            
            data = {
                'source_type': 'logistics',
                'source_id': 123,
                'source_no': 'LS20250120001',
                'payee_type': 'logistics_provider',
                'payee_id': provider.id,
                'payee_name': provider.provider_name,
                'bank_name': provider.bank_name,
                'bank_account': provider.bank_account,
                'bank_account_name': provider.bank_account_name,
                'payable_amount': Decimal('5000.00'),
                'currency': 'CNY',
                'priority': 3,
                'notes': '测试应付单'
            }
            
            # 创建应付单
            payable = PayableService.create_payable(data, created_by=user.id)
            
            # 验证
            assert payable.payable_no.startswith('AP')
            assert payable.source_type == 'logistics'
            assert payable.source_id == 123
            assert payable.payee_id == provider.id
            assert payable.payable_amount == Decimal('5000.00')
            assert payable.paid_amount == Decimal('0.00')
            assert payable.status == PayableStatus.PENDING.value
            assert payable.created_by_id == user.id
    
    def test_approve_payable(self, app):
        """测试审批应付单（批准）"""
        with app.app_context():
            # 准备测试数据
            payable = FinPayableFactory(status=PayableStatus.PENDING.value)
            user = UserFactory()
            
            # 审批批准
            approved_payable = PayableService.approve_payable(
                payable_id=payable.id,
                action='approve',
                approved_by=user.id
            )
            
            # 验证
            assert approved_payable.status == PayableStatus.APPROVED.value
            assert approved_payable.approved_by_id == user.id
            assert approved_payable.approved_at is not None
    
    def test_reject_payable(self, app):
        """测试审批应付单（驳回）"""
        with app.app_context():
            # 准备测试数据
            payable = FinPayableFactory(status=PayableStatus.PENDING.value)
            user = UserFactory()
            
            # 审批驳回
            rejected_payable = PayableService.approve_payable(
                payable_id=payable.id,
                action='reject',
                approved_by=user.id,
                rejection_reason='金额不符'
            )
            
            # 验证
            assert rejected_payable.status == PayableStatus.REJECTED.value
            assert rejected_payable.approved_by_id == user.id
            assert rejected_payable.rejection_reason == '金额不符'
    
    def test_approve_and_add_to_pool(self, app):
        """测试审批并加入付款池"""
        with app.app_context():
            # 准备测试数据
            payable = FinPayableFactory(
                status=PayableStatus.PENDING.value,
                payable_amount=Decimal('3000.00')
            )
            pool = FinPaymentPoolFactory(
                status=PaymentPoolStatus.DRAFT.value,
                total_amount=Decimal('0.00'),
                total_count=0
            )
            user = UserFactory()
            
            # 审批并加入池
            approved_payable = PayableService.approve_payable(
                payable_id=payable.id,
                action='approve',
                approved_by=user.id,
                add_to_pool=True,
                pool_id=pool.id
            )
            
            # 验证应付单
            assert approved_payable.status == PayableStatus.IN_POOL.value
            assert approved_payable.payment_pool_id == pool.id
            
            # 验证付款池统计
            from app.extensions import db
            db.session.refresh(pool)
            assert pool.total_amount == Decimal('3000.00')
            assert pool.total_count == 1
    
    def test_add_payable_to_pool(self, app):
        """测试将应付单加入付款池"""
        with app.app_context():
            # 准备测试数据
            payable = FinPayableFactory(
                status=PayableStatus.APPROVED.value,
                payable_amount=Decimal('2000.00')
            )
            pool = FinPaymentPoolFactory(
                status=PaymentPoolStatus.DRAFT.value,
                total_amount=Decimal('0.00'),
                total_count=0
            )
            
            # 加入付款池
            updated_payable = PayableService.add_payable_to_pool(payable.id, pool.id)
            
            # 验证
            assert updated_payable.status == PayableStatus.IN_POOL.value
            assert updated_payable.payment_pool_id == pool.id
            
            # 验证池统计
            from app.extensions import db
            db.session.refresh(pool)
            assert pool.total_amount == Decimal('2000.00')
            assert pool.total_count == 1
    
    def test_mark_as_paid(self, app):
        """测试标记已付款"""
        with app.app_context():
            # 准备测试数据
            payable = FinPayableFactory(
                status=PayableStatus.APPROVED.value,
                payable_amount=Decimal('5000.00'),
                paid_amount=Decimal('0.00')
            )
            
            # 标记已付款
            paid_payable = PayableService.mark_as_paid(
                payable_id=payable.id,
                paid_amount=Decimal('5000.00')
            )
            
            # 验证
            assert paid_payable.status == PayableStatus.PAID.value
            assert paid_payable.paid_amount == Decimal('5000.00')
            assert paid_payable.paid_at is not None
            assert paid_payable.is_fully_paid is True
    
    def test_mark_as_partial_paid(self, app):
        """测试部分付款"""
        with app.app_context():
            # 准备测试数据
            payable = FinPayableFactory(
                status=PayableStatus.APPROVED.value,
                payable_amount=Decimal('5000.00'),
                paid_amount=Decimal('0.00')
            )
            
            # 第一次部分付款
            partially_paid = PayableService.mark_as_paid(
                payable_id=payable.id,
                paid_amount=Decimal('3000.00')
            )
            
            # 验证
            assert partially_paid.status == PayableStatus.APPROVED.value  # 还未全额付款
            assert partially_paid.paid_amount == Decimal('3000.00')
            assert partially_paid.remaining_amount == Decimal('2000.00')
            assert partially_paid.is_fully_paid is False
            
            # 第二次付清尾款
            fully_paid = PayableService.mark_as_paid(
                payable_id=payable.id,
                paid_amount=Decimal('2000.00')
            )
            
            # 验证
            assert fully_paid.status == PayableStatus.PAID.value
            assert fully_paid.paid_amount == Decimal('5000.00')
            assert fully_paid.is_fully_paid is True
    
    def test_reject_payable_notifies_logistics(self, app):
        """测试驳回应付单时回调通知物流模块"""
        with app.app_context():
            # 准备测试数据：创建物流对账单并提交财务
            from app.models.logistics.logistics_statement import StatementStatus
            provider = LogisticsProviderFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.SUBMITTED.value,  # 已提交财务
                total_amount=Decimal('6000.00')
            )
            
            payable = FinPayableFactory(
                source_type='logistics',
                source_id=statement.id,
                status=PayableStatus.PENDING.value,
                payable_amount=Decimal('6000.00')
            )
            
            # 更新对账单的财务关联
            statement.finance_payable_id = payable.id
            from app.extensions import db
            db.session.commit()
            
            user = UserFactory()
            
            # 驳回应付单
            PayableService.approve_payable(
                payable_id=payable.id,
                action='reject',
                approved_by=user.id,
                rejection_reason='金额有误'
            )
            
            # 验证对账单状态已回退
            db.session.refresh(statement)
            assert statement.status == StatementStatus.CONFIRMED.value
            assert statement.finance_payable_id is None
            assert '金额有误' in (statement.notes or '')
    
    def test_paid_payable_notifies_logistics(self, app):
        """测试付款后回调通知物流模块更新服务状态"""
        with app.app_context():
            # 准备测试数据
            from app.models.logistics.logistics_statement import StatementStatus
            from app.models.logistics.shipment_logistics_service import ServiceStatus
            from app.models.logistics.logistics_statement import statement_service_relation
            from tests.factories import ShipmentOrderFactory, ShipmentLogisticsServiceFactory
            
            provider = LogisticsProviderFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.SUBMITTED.value,
                total_amount=Decimal('4000.00')
            )
            
            shipment = ShipmentOrderFactory()
            service = ShipmentLogisticsServiceFactory(
                shipment=shipment,
                logistics_provider=provider,
                actual_amount=Decimal('4000.00'),
                status=ServiceStatus.RECONCILED.value
            )
            
            # 关联服务到对账单
            from app.extensions import db
            db.session.execute(
                statement_service_relation.insert().values(
                    statement_id=statement.id,
                    logistics_service_id=service.id,
                    reconciled_amount=Decimal('4000.00')
                )
            )
            db.session.commit()
            
            payable = FinPayableFactory(
                source_type='logistics',
                source_id=statement.id,
                status=PayableStatus.APPROVED.value,
                payable_amount=Decimal('4000.00')
            )
            
            statement.finance_payable_id = payable.id
            db.session.commit()
            
            # 标记已付款
            PayableService.mark_as_paid(
                payable_id=payable.id,
                paid_amount=Decimal('4000.00')
            )
            
            # 验证对账单状态
            db.session.refresh(statement)
            assert statement.status == StatementStatus.PAID.value
            
            # 验证物流服务状态
            db.session.refresh(service)
            assert service.status == ServiceStatus.PAID.value
            assert service.paid_at is not None
    
    def test_get_payable_by_id(self, app):
        """测试获取应付单详情"""
        with app.app_context():
            # 准备测试数据
            payable = FinPayableFactory()
            
            # 获取详情
            retrieved = PayableService.get_payable_by_id(payable.id)
            
            # 验证
            assert retrieved is not None
            assert retrieved.id == payable.id
            assert retrieved.payable_no == payable.payable_no

