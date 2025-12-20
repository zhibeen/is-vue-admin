"""
物流服务商模块测试
测试物流服务商的CRUD操作
"""
import pytest
from app.models.logistics import LogisticsProvider
from app.services.logistics.logistics_provider_service import LogisticsProviderService
from app.errors import BusinessError


class TestLogisticsProvider:
    """物流服务商测试类"""
    
    def test_create_provider(self, app, db_session):
        """测试创建物流服务商"""
        data = {
            'provider_name': '测试物流公司',
            'provider_code': 'TEST001',
            'service_type': 'domestic_trucking',
            'payment_method': 'postpaid',
            'settlement_cycle': 'monthly',
            'contact_name': '张三',
            'contact_phone': '13800138000',
            'is_active': True
        }
        
        provider = LogisticsProviderService.create_provider(data)
        
        assert provider.id is not None
        assert provider.provider_name == '测试物流公司'
        assert provider.provider_code == 'TEST001'
        assert provider.is_active is True
    
    def test_create_duplicate_provider_code(self, app, db_session):
        """测试创建重复编码的服务商"""
        data = {
            'provider_name': '物流公司A',
            'provider_code': 'DUP001',
            'service_type': 'domestic_trucking',
        }
        
        # 第一次创建成功
        LogisticsProviderService.create_provider(data)
        
        # 第二次创建应失败
        with pytest.raises(BusinessError) as exc_info:
            LogisticsProviderService.create_provider(data)
        
        assert '服务商编码已存在' in str(exc_info.value)
    
    def test_get_provider_by_id(self, app, db_session):
        """测试根据ID获取服务商"""
        # 创建服务商
        data = {
            'provider_name': '测试公司',
            'provider_code': 'GET001',
            'service_type': 'international_sea',
        }
        provider = LogisticsProviderService.create_provider(data)
        
        # 获取服务商
        found = LogisticsProviderService.get_provider_by_id(provider.id)
        
        assert found is not None
        assert found.provider_code == 'GET001'
    
    def test_get_provider_by_code(self, app, db_session):
        """测试根据编码获取服务商"""
        data = {
            'provider_name': '编码测试公司',
            'provider_code': 'CODE001',
            'service_type': 'international_air',
        }
        LogisticsProviderService.create_provider(data)
        
        found = LogisticsProviderService.get_provider_by_code('CODE001')
        
        assert found is not None
        assert found.provider_name == '编码测试公司'
    
    def test_update_provider(self, app, db_session):
        """测试更新服务商"""
        # 创建服务商
        data = {
            'provider_name': '原名称',
            'provider_code': 'UPD001',
            'service_type': 'domestic_trucking',
            'is_active': True
        }
        provider = LogisticsProviderService.create_provider(data)
        
        # 更新服务商
        update_data = {
            'provider_name': '新名称',
            'contact_name': '李四',
            'is_active': False
        }
        updated = LogisticsProviderService.update_provider(provider.id, update_data)
        
        assert updated.provider_name == '新名称'
        assert updated.contact_name == '李四'
        assert updated.is_active is False
        assert updated.provider_code == 'UPD001'  # 编码不变
    
    def test_delete_provider(self, app, db_session):
        """测试删除服务商"""
        data = {
            'provider_name': '待删除公司',
            'provider_code': 'DEL001',
            'service_type': 'customs_clearance',
        }
        provider = LogisticsProviderService.create_provider(data)
        provider_id = provider.id
        
        # 删除服务商
        LogisticsProviderService.delete_provider(provider_id)
        
        # 验证已删除
        found = LogisticsProviderService.get_provider_by_id(provider_id)
        assert found is None
    
    def test_toggle_active_status(self, app, db_session):
        """测试切换启用状态"""
        data = {
            'provider_name': '状态测试公司',
            'provider_code': 'TOG001',
            'service_type': 'destination_delivery',
            'is_active': True
        }
        provider = LogisticsProviderService.create_provider(data)
        
        # 切换为停用
        updated = LogisticsProviderService.toggle_active_status(provider.id)
        assert updated.is_active is False
        
        # 再切换回启用
        updated = LogisticsProviderService.toggle_active_status(provider.id)
        assert updated.is_active is True
    
    def test_get_all_providers_with_filter(self, app, db_session):
        """测试带筛选条件获取服务商列表"""
        # 创建多个服务商
        LogisticsProviderService.create_provider({
            'provider_name': 'A公司',
            'provider_code': 'LST001',
            'service_type': 'domestic_trucking',
            'is_active': True
        })
        LogisticsProviderService.create_provider({
            'provider_name': 'B公司',
            'provider_code': 'LST002',
            'service_type': 'domestic_trucking',
            'is_active': False
        })
        LogisticsProviderService.create_provider({
            'provider_name': 'C公司',
            'provider_code': 'LST003',
            'service_type': 'international_sea',
            'is_active': True
        })
        
        # 测试按启用状态筛选
        active_providers = LogisticsProviderService.get_all_providers(is_active=True)
        assert len(active_providers) >= 2
        
        # 测试按服务类型筛选
        trucking_providers = LogisticsProviderService.get_all_providers(
            service_type='domestic_trucking'
        )
        assert len(trucking_providers) >= 2
        
        # 测试组合筛选
        active_trucking = LogisticsProviderService.get_all_providers(
            is_active=True,
            service_type='domestic_trucking'
        )
        assert len(active_trucking) >= 1

