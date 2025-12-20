"""
物流服务明细模块测试
测试发货单物流服务的添加、更新、确认等操作
"""
import pytest
from decimal import Decimal
from app.models.logistics import (
    ShipmentLogisticsService,
    ShipmentOrder,
    LogisticsProvider
)
from app.services.logistics.shipment_logistics_service import ShipmentLogisticsServiceService
from app.errors import BusinessError


@pytest.fixture
def sample_shipment(app, db_session):
    """创建测试用发货单"""
    shipment = ShipmentOrder(
        shipment_no='TEST-SHIP-001',
        source='manual',
        status='confirmed',
        shipper_company_id=1,
        total_packages=10
    )
    db_session.add(shipment)
    db_session.commit()
    return shipment


@pytest.fixture
def sample_provider(app, db_session):
    """创建测试用物流服务商"""
    provider = LogisticsProvider(
        provider_name='测试物流',
        provider_code='TEST-PROV-001',
        service_type='domestic_trucking',
        is_active=True
    )
    db_session.add(provider)
    db_session.commit()
    return provider


class TestShipmentLogisticsService:
    """物流服务明细测试类"""
    
    def test_add_service(self, app, db_session, sample_shipment, sample_provider):
        """测试添加物流服务"""
        data = {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'service_description': '深圳至上海陆运',
            'estimated_amount': Decimal('5000.00'),
            'currency': 'CNY',
            'payment_method': 'postpaid'
        }
        
        service = ShipmentLogisticsServiceService.add_service(sample_shipment.id, data)
        
        assert service.id is not None
        assert service.shipment_id == sample_shipment.id
        assert service.logistics_provider_id == sample_provider.id
        assert service.estimated_amount == Decimal('5000.00')
        assert service.status == 'pending'
    
    def test_add_service_to_nonexistent_shipment(self, app, db_session, sample_provider):
        """测试为不存在的发货单添加服务"""
        data = {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'estimated_amount': Decimal('5000.00'),
        }
        
        with pytest.raises(BusinessError) as exc_info:
            ShipmentLogisticsServiceService.add_service(99999, data)
        
        assert '发货单不存在' in str(exc_info.value)
    
    def test_get_services_by_shipment(self, app, db_session, sample_shipment, sample_provider):
        """测试获取发货单的所有物流服务"""
        # 添加多个服务
        for i in range(3):
            data = {
                'logistics_provider_id': sample_provider.id,
                'service_type': 'domestic_trucking',
                'estimated_amount': Decimal(f'{1000 * (i + 1)}.00'),
            }
            ShipmentLogisticsServiceService.add_service(sample_shipment.id, data)
        
        # 获取服务列表
        services = ShipmentLogisticsServiceService.get_services_by_shipment(sample_shipment.id)
        
        assert len(services) == 3
        assert all(s.shipment_id == sample_shipment.id for s in services)
    
    def test_update_service(self, app, db_session, sample_shipment, sample_provider):
        """测试更新物流服务"""
        # 创建服务
        data = {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'estimated_amount': Decimal('5000.00'),
        }
        service = ShipmentLogisticsServiceService.add_service(sample_shipment.id, data)
        
        # 更新服务
        update_data = {
            'actual_amount': Decimal('4800.00'),
            'service_description': '更新后的描述',
            'notes': '测试备注'
        }
        updated = ShipmentLogisticsServiceService.update_service(service.id, update_data)
        
        assert updated.actual_amount == Decimal('4800.00')
        assert updated.service_description == '更新后的描述'
        assert updated.notes == '测试备注'
    
    def test_delete_service(self, app, db_session, sample_shipment, sample_provider):
        """测试删除物流服务"""
        data = {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'estimated_amount': Decimal('5000.00'),
        }
        service = ShipmentLogisticsServiceService.add_service(sample_shipment.id, data)
        service_id = service.id
        
        # 删除服务
        ShipmentLogisticsServiceService.delete_service(service_id)
        
        # 验证已删除
        found = ShipmentLogisticsServiceService.get_service_by_id(service_id)
        assert found is None
    
    def test_delete_reconciled_service_should_fail(self, app, db_session, sample_shipment, sample_provider):
        """测试删除已对账的服务应失败"""
        data = {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'estimated_amount': Decimal('5000.00'),
        }
        service = ShipmentLogisticsServiceService.add_service(sample_shipment.id, data)
        
        # 标记为已对账
        service.status = 'reconciled'
        db_session.commit()
        
        # 尝试删除应失败
        with pytest.raises(BusinessError) as exc_info:
            ShipmentLogisticsServiceService.delete_service(service.id)
        
        assert '已对账' in str(exc_info.value)
    
    def test_confirm_service(self, app, db_session, sample_shipment, sample_provider):
        """测试确认物流服务"""
        data = {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'estimated_amount': Decimal('5000.00'),
        }
        service = ShipmentLogisticsServiceService.add_service(sample_shipment.id, data)
        
        # 确认服务
        confirmed = ShipmentLogisticsServiceService.confirm_service(service.id)
        
        assert confirmed.status == 'confirmed'
        assert confirmed.confirmed_at is not None
    
    def test_calculate_total_cost(self, app, db_session, sample_shipment, sample_provider):
        """测试计算物流总费用"""
        # 添加多个服务
        ShipmentLogisticsServiceService.add_service(sample_shipment.id, {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'estimated_amount': Decimal('1000.00'),
            'actual_amount': Decimal('950.00'),
        })
        ShipmentLogisticsServiceService.add_service(sample_shipment.id, {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'customs_clearance',
            'estimated_amount': Decimal('2000.00'),
            'actual_amount': Decimal('2100.00'),
        })
        ShipmentLogisticsServiceService.add_service(sample_shipment.id, {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'international_air',
            'estimated_amount': Decimal('5000.00'),
            # 没有实际费用
        })
        
        # 计算总费用（使用实际费用优先）
        total = ShipmentLogisticsServiceService.calculate_total_cost(sample_shipment.id, use_actual=True)
        
        # 950 + 2100 + 5000 = 8050
        assert total == Decimal('8050.00')
        
        # 计算总费用（仅使用预估费用）
        total_estimated = ShipmentLogisticsServiceService.calculate_total_cost(
            sample_shipment.id, 
            use_actual=False
        )
        
        # 1000 + 2000 + 5000 = 8000
        assert total_estimated == Decimal('8000.00')
    
    def test_mark_as_reconciled(self, app, db_session, sample_shipment, sample_provider):
        """测试标记为已对账"""
        data = {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'estimated_amount': Decimal('5000.00'),
        }
        service = ShipmentLogisticsServiceService.add_service(sample_shipment.id, data)
        
        # 先确认
        ShipmentLogisticsServiceService.confirm_service(service.id)
        
        # 标记为已对账
        reconciled = ShipmentLogisticsServiceService.mark_as_reconciled(service.id)
        
        assert reconciled.status == 'reconciled'
        assert reconciled.reconciled_at is not None
    
    def test_mark_as_paid(self, app, db_session, sample_shipment, sample_provider):
        """测试标记为已付款"""
        data = {
            'logistics_provider_id': sample_provider.id,
            'service_type': 'domestic_trucking',
            'estimated_amount': Decimal('5000.00'),
        }
        service = ShipmentLogisticsServiceService.add_service(sample_shipment.id, data)
        
        # 先确认
        ShipmentLogisticsServiceService.confirm_service(service.id)
        
        # 标记为已对账
        ShipmentLogisticsServiceService.mark_as_reconciled(service.id)
        
        # 标记为已付款
        paid = ShipmentLogisticsServiceService.mark_as_paid(service.id)
        
        assert paid.status == 'paid'
        assert paid.paid_at is not None

