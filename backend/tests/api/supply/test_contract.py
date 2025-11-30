import pytest
from app.extensions import db
from app.models.supply import ScmDeliveryContract, ScmDeliveryItem
from app.models.serc.enums import ContractStatus

@pytest.fixture
def supply_data(db_session, supplier_factory, product_factory):
    # Ensure supplier and product are created within the session
    supplier = supplier_factory()
    product = product_factory()
    db_session.commit()
    return {'supplier': supplier, 'product': product}

class TestSupplyContractAPI:
    
    def test_create_contract(self, client, token_headers, supply_data):
        """测试创建 L1 交付合同"""
        url = '/api/v1/supply/contracts'
        data = {
            'supplier_id': supply_data['supplier'].id,
            'currency': 'CNY',
            'event_date': '2023-10-01',
            'items': [
                {
                    'product_id': supply_data['product'].id,
                    'confirmed_qty': 100,
                    'unit_price': 50.00
                }
            ]
        }
        
        resp = client.post(url, json=data, headers=token_headers)
        assert resp.status_code == 201
        assert resp.json['code'] == 0
        
        contract_id = resp.json['data']['id']
        contract = db.session.get(ScmDeliveryContract, contract_id)
        assert contract is not None
        assert contract.total_amount == 5000.00
        assert contract.status == ContractStatus.PENDING.value
        assert len(contract.items) == 1

    def test_get_contract_list(self, client, token_headers, supply_data):
        """测试获取合同列表"""
        # 先创建一个
        contract = ScmDeliveryContract(
            contract_no='CON-001',
            supplier_id=supply_data['supplier'].id,
            total_amount=1000,
            status=ContractStatus.PENDING.value
        )
        db.session.add(contract)
        db.session.commit()
        
        url = '/api/v1/supply/contracts'
        resp = client.get(url, headers=token_headers)
        
        assert resp.status_code == 200
        assert len(resp.json['data']) >= 1
        # Fix: check inside items if paginated or direct list
        # Assuming pagination: {'data': {'items': [...], ...}} or list in data
        # Based on previous pattern, it's likely pagination.
        # But wait, routes.py: return {'data': pagination.items}
        # So it returns a list directly inside data.
        assert resp.json['data'][0]['contract_no'] == 'CON-001'
