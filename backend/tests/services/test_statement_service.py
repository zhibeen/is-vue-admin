"""
物流对账单服务层测试
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from app.services.logistics.statement_service import StatementService
from app.models.logistics.logistics_statement import LogisticsStatement, StatementStatus
from app.models.logistics.shipment_logistics_service import ShipmentLogisticsService, ServiceStatus
from app.errors import BusinessError
from tests.factories import (
    LogisticsProviderFactory,
    ShipmentOrderFactory,
    ShipmentLogisticsServiceFactory,
    LogisticsStatementFactory,
    UserFactory
)


class TestStatementService:
    """测试物流对账单服务"""
    
    def test_generate_statement_no(self, app):
        """测试生成对账单号"""
        with app.app_context():
            statement_no = StatementService.generate_statement_no()
            assert statement_no.startswith('LS')
            assert len(statement_no) == 14  # LS(2) + YYYYMMDD(8) + 4位数字(4)
    
    def test_create_draft_statement(self, app):
        """测试创建对账单草稿"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            user = UserFactory()
            
            data = {
                'logistics_provider_id': provider.id,
                'period_start': date(2025, 1, 1),
                'period_end': date(2025, 1, 31),
                'auto_include_services': False
            }
            
            # 创建对账单
            statement = StatementService.create_draft_statement(data, created_by=user.id)
            
            # 验证
            assert statement.statement_no.startswith('LS')
            assert statement.logistics_provider_id == provider.id
            assert statement.statement_period_start == date(2025, 1, 1)
            assert statement.statement_period_end == date(2025, 1, 31)
            assert statement.status == StatementStatus.DRAFT.value
            assert statement.total_amount == Decimal('0')
            assert statement.created_by_id == user.id
    
    def test_create_statement_with_auto_include_services(self, app):
        """测试创建对账单时自动包含物流服务"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            shipment = ShipmentOrderFactory()
            user = UserFactory()
            
            # 创建3个已确认的物流服务
            service1 = ShipmentLogisticsServiceFactory(
                shipment=shipment,
                logistics_provider=provider,
                actual_amount=Decimal('1000.00'),
                status=ServiceStatus.CONFIRMED.value,
                confirmed_at=datetime(2025, 1, 15)
            )
            service2 = ShipmentLogisticsServiceFactory(
                shipment=shipment,
                logistics_provider=provider,
                actual_amount=Decimal('2000.00'),
                status=ServiceStatus.CONFIRMED.value,
                confirmed_at=datetime(2025, 1, 20)
            )
            # 这个不应该被包含（不同物流商）
            other_provider = LogisticsProviderFactory()
            service3 = ShipmentLogisticsServiceFactory(
                shipment=shipment,
                logistics_provider=other_provider,
                actual_amount=Decimal('500.00'),
                status=ServiceStatus.CONFIRMED.value,
                confirmed_at=datetime(2025, 1, 25)
            )
            
            data = {
                'logistics_provider_id': provider.id,
                'period_start': date(2025, 1, 1),
                'period_end': date(2025, 1, 31),
                'auto_include_services': True
            }
            
            # 创建对账单
            statement = StatementService.create_draft_statement(data, created_by=user.id)
            
            # 验证
            assert statement.total_amount == Decimal('3000.00')  # 只包含前两个
            assert len(statement.logistics_services) == 2
            assert service1 in statement.logistics_services
            assert service2 in statement.logistics_services
            assert service3 not in statement.logistics_services
    
    def test_add_service_to_statement(self, app):
        """测试添加物流服务到对账单"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.DRAFT.value,
                total_amount=Decimal('0')
            )
            shipment = ShipmentOrderFactory()
            service = ShipmentLogisticsServiceFactory(
                shipment=shipment,
                logistics_provider=provider,
                actual_amount=Decimal('1500.00'),
                status=ServiceStatus.CONFIRMED.value
            )
            
            # 添加服务
            StatementService.add_service_to_statement(
                statement_id=statement.id,
                service_id=service.id
            )
            
            # 刷新对象
            from app.extensions import db
            db.session.refresh(statement)
            
            # 验证
            assert statement.total_amount == Decimal('1500.00')
            assert len(statement.logistics_services) == 1
            assert service in statement.logistics_services
    
    def test_confirm_statement(self, app):
        """测试确认对账单"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.DRAFT.value,
                total_amount=Decimal('5000.00'),
                attachment_ids=[1, 2]  # 模拟已上传附件
            )
            shipment = ShipmentOrderFactory()
            service = ShipmentLogisticsServiceFactory(
                shipment=shipment,
                logistics_provider=provider,
                actual_amount=Decimal('5000.00'),
                status=ServiceStatus.CONFIRMED.value
            )
            # 关联服务到对账单
            from app.models.logistics.logistics_statement import statement_service_relation
            from app.extensions import db
            db.session.execute(
                statement_service_relation.insert().values(
                    statement_id=statement.id,
                    logistics_service_id=service.id,
                    reconciled_amount=Decimal('5000.00')
                )
            )
            db.session.commit()
            
            user = UserFactory()
            
            # 确认对账单
            confirmed_statement = StatementService.confirm_statement(
                statement_id=statement.id,
                confirmed_by=user.id
            )
            
            # 验证
            assert confirmed_statement.status == StatementStatus.CONFIRMED.value
            assert confirmed_statement.confirmed_by_id == user.id
            assert confirmed_statement.confirmed_at is not None
    
    def test_confirm_statement_without_attachment(self, app):
        """测试确认对账单失败：缺少附件"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.DRAFT.value,
                total_amount=Decimal('5000.00'),
                attachment_ids=None  # 没有附件
            )
            user = UserFactory()
            
            # 尝试确认对账单（应该失败）
            with pytest.raises(BusinessError) as exc_info:
                StatementService.confirm_statement(
                    statement_id=statement.id,
                    confirmed_by=user.id
                )
            
            assert exc_info.value.status_code == 400
            assert '请上传对账单附件' in exc_info.value.message
    
    def test_submit_to_finance(self, app):
        """测试提交对账单到财务"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory(
                bank_name='中国工商银行',
                bank_account='6222000000000001',
                bank_account_name='测试物流商',
                settlement_cycle='monthly'
            )
            user = UserFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.CONFIRMED.value,
                total_amount=Decimal('8000.00'),
                confirmed_by_id=user.id,
                confirmed_at=datetime.now()
            )
            shipment = ShipmentOrderFactory()
            service = ShipmentLogisticsServiceFactory(
                shipment=shipment,
                logistics_provider=provider,
                actual_amount=Decimal('8000.00'),
                status=ServiceStatus.CONFIRMED.value
            )
            # 关联服务
            from app.models.logistics.logistics_statement import statement_service_relation
            from app.extensions import db
            db.session.execute(
                statement_service_relation.insert().values(
                    statement_id=statement.id,
                    logistics_service_id=service.id,
                    reconciled_amount=Decimal('8000.00')
                )
            )
            db.session.commit()
            
            # 提交财务
            result = StatementService.submit_to_finance(statement.id)
            
            # 验证
            assert result['statement_id'] == statement.id
            assert 'finance_payable_id' in result
            assert 'finance_payable_no' in result
            assert result['finance_payable_no'].startswith('AP')
            
            # 验证对账单状态已更新
            db.session.refresh(statement)
            assert statement.status == StatementStatus.SUBMITTED.value
            assert statement.finance_payable_id == result['finance_payable_id']
            assert statement.submitted_to_finance_at is not None
            
            # 验证物流服务状态已更新
            db.session.refresh(service)
            assert service.status == ServiceStatus.RECONCILED.value
            assert service.reconciled_at is not None
            
            # 验证应付单已创建
            from app.models.serc.payable import FinPayable
            payable = db.session.get(FinPayable, result['finance_payable_id'])
            assert payable is not None
            assert payable.source_type == 'logistics'
            assert payable.source_id == statement.id
            assert payable.payable_amount == Decimal('8000.00')
            assert payable.payee_type == 'logistics_provider'
            assert payable.payee_id == provider.id
    
    def test_remove_service_from_statement(self, app):
        """测试从对账单移除物流服务"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.DRAFT.value,
                total_amount=Decimal('1000.00')
            )
            shipment = ShipmentOrderFactory()
            service = ShipmentLogisticsServiceFactory(
                shipment=shipment,
                logistics_provider=provider,
                actual_amount=Decimal('1000.00'),
                status=ServiceStatus.CONFIRMED.value
            )
            # 关联服务
            from app.models.logistics.logistics_statement import statement_service_relation
            from app.extensions import db
            db.session.execute(
                statement_service_relation.insert().values(
                    statement_id=statement.id,
                    logistics_service_id=service.id,
                    reconciled_amount=Decimal('1000.00')
                )
            )
            db.session.commit()
            
            # 移除服务
            StatementService.remove_service_from_statement(statement.id, service.id)
            
            # 刷新对象
            db.session.refresh(statement)
            
            # 验证
            assert statement.total_amount == Decimal('0')
            assert len(statement.logistics_services) == 0
    
    def test_update_statement(self, app):
        """测试更新对账单"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.DRAFT.value,
                notes='原备注'
            )
            
            # 更新对账单
            updated_statement = StatementService.update_statement(
                statement_id=statement.id,
                data={
                    'notes': '更新后的备注',
                    'attachment_ids': [10, 20]
                }
            )
            
            # 验证
            assert updated_statement.notes == '更新后的备注'
            assert updated_statement.attachment_ids == [10, 20]
    
    def test_delete_statement(self, app):
        """测试删除对账单"""
        with app.app_context():
            # 准备测试数据
            provider = LogisticsProviderFactory()
            statement = LogisticsStatementFactory(
                logistics_provider=provider,
                status=StatementStatus.DRAFT.value
            )
            statement_id = statement.id
            
            # 删除对账单
            StatementService.delete_statement(statement_id)
            
            # 验证
            from app.extensions import db
            deleted = db.session.get(LogisticsStatement, statement_id)
            assert deleted is None

