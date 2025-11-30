import pytest
from decimal import Decimal
from app.services.serc.supply_service import supply_service
from app.models.supply import ScmDeliveryContract, ScmContractChangeLog
from app.errors import StaleDataError
from tests.factories import ScmDeliveryContractFactory, ProductFactory

@pytest.fixture
def contract(db_session):
    return ScmDeliveryContractFactory(version=1, total_amount=Decimal('100.00'))

def test_optimistic_locking_success(db_session, contract):
    """测试乐观锁：版本号匹配，更新成功"""
    data = {
        'version': 1,
        'notes': 'Updated notes',
        'change_reason': 'Test Update'
    }
    
    updated_contract = supply_service.update_contract(contract.id, data, user_id=1)
    
    assert updated_contract.version == 2
    assert updated_contract.notes == 'Updated notes'
    
    # 验证日志
    log = db_session.query(ScmContractChangeLog).filter_by(contract_id=contract.id).first()
    assert log is not None
    assert log.content_before['version'] == 1
    assert log.content_after['version'] == 2
    assert log.change_reason == 'Test Update'

def test_optimistic_locking_failure(db_session, contract):
    """测试乐观锁：版本号不匹配，更新失败"""
    data = {
        'version': 0, # Wrong version
        'notes': 'Should fail'
    }
    
    with pytest.raises(StaleDataError) as exc:
        supply_service.update_contract(contract.id, data, user_id=1)
    
    assert "数据版本不一致" in exc.value.message
        
    # Verify no change
    db_session.refresh(contract)
    assert contract.version == 1
    assert contract.notes != 'Should fail'

def test_update_contract_items(db_session, contract):
    """测试更新合同明细"""
    product = ProductFactory()
    
    data = {
        'version': 1,
        'items': [
            {
                'product_id': product.id,
                'confirmed_qty': 5,
                'unit_price': 20,
                'notes': 'New Item'
            }
        ]
    }
    
    updated = supply_service.update_contract(contract.id, data)
    
    assert len(updated.items) == 1
    assert updated.items[0].product_id == product.id
    assert updated.total_amount == 100 # 5 * 20
    assert updated.version == 2
    
    # Verify log contains item changes
    log = db_session.query(ScmContractChangeLog).filter_by(contract_id=contract.id).first()
    assert len(log.content_after['items']) == 1

