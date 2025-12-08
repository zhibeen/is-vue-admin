import pytest
from decimal import Decimal
from app.models.supply import ScmDeliveryContract, ScmDeliveryContractItem
from app.models.purchase.supplier import SysSupplier
from app.models.product import Product, SysTaxCategory
from app.models.serc.finance import FinSupplyContract
from app.services.serc.finance_service import finance_service
from app.extensions import db

@pytest.fixture
def setup_l15_data(db_session):
    """准备 L1.5 测试数据环境"""
    
    # 1. Tax Category
    tax_cat = SysTaxCategory(
        code='109010101', 
        name='Test Tax Category', 
        reference_rate=Decimal('0.13')
    )
    db_session.add(tax_cat)
    db_session.flush()

    # 2. Product
    product = Product(
        sku='TEST-SKU-001',
        name='Test Product',
        declared_name='Test Declared Name',
        declared_unit='PCS',
        tax_category_id=tax_cat.id
    )
    db_session.add(product)
    db_session.flush()

    # 3. Supplier (General Taxpayer)
    supplier_gen = SysSupplier(
        code='TEST-SUP-GEN',
        name='General Supplier',
        taxpayer_type='general',
        default_vat_rate=Decimal('0.13')
    )
    db_session.add(supplier_gen)
    
    # 4. Supplier (Small Taxpayer)
    supplier_small = SysSupplier(
        code='TEST-SUP-SMALL',
        name='Small Supplier',
        taxpayer_type='small',
        default_vat_rate=Decimal('0.03')
    )
    db_session.add(supplier_small)
    db_session.flush()

    return {
        'product': product,
        'tax_cat': tax_cat,
        'supplier_gen': supplier_gen,
        'supplier_small': supplier_small
    }

def test_preview_aggregation_general_taxpayer(client, setup_l15_data, db_session):
    """测试一般纳税人聚合逻辑"""
    data = setup_l15_data
    supplier = data['supplier_gen']
    product = data['product']

    # Create L1 Contract
    l1 = ScmDeliveryContract(
        contract_no='L1-TEST-001',
        supplier_id=supplier.id,
        total_amount=Decimal('1130.00'),
        currency='CNY'
    )
    db_session.add(l1)
    db_session.flush()

    # Add Items (Same Product, Split Lines)
    item1 = ScmDeliveryContractItem(
        l1_contract_id=l1.id,  # Changed from delivery_contract_id
        product_id=product.id,
        confirmed_qty=Decimal('50'), # Changed from quantity
        unit_price=Decimal('11.30'), # Changed from price
        total_price=Decimal('565.00') # Changed from amount
    )
    item2 = ScmDeliveryContractItem(
        l1_contract_id=l1.id,  # Changed from delivery_contract_id
        product_id=product.id,
        confirmed_qty=Decimal('50'), # Changed from quantity
        unit_price=Decimal('11.30'), # Changed from price
        total_price=Decimal('565.00') # Changed from amount
    )
    db_session.add_all([item1, item2])
    db_session.commit()

    # Call Preview Service
    result = finance_service.preview_supply_contract_from_l1(l1.id)['data']

    assert result['is_balanced'] is True
    assert len(result['items']) == 1  # Should aggregate to 1 line
    
    aggregated = result['items'][0]
    assert aggregated['invoice_name'] == 'Test Declared Name'
    assert aggregated['tax_code'] == '109010101'
    assert aggregated['tax_rate'] == Decimal('0.13') # From Supplier
    assert aggregated['quantity'] == Decimal('100')
    assert aggregated['amount'] == Decimal('1130.00')

def test_preview_aggregation_small_taxpayer(client, setup_l15_data, db_session):
    """测试小规模纳税人聚合逻辑 (税率变更为 0.03)"""
    data = setup_l15_data
    supplier = data['supplier_small']
    product = data['product']

    # Create L1 Contract
    l1 = ScmDeliveryContract(
        contract_no='L1-TEST-002',
        supplier_id=supplier.id,
        total_amount=Decimal('1030.00'),
        currency='CNY'
    )
    db_session.add(l1)
    db_session.flush()

    item1 = ScmDeliveryContractItem(
        l1_contract_id=l1.id, # Changed from delivery_contract_id
        product_id=product.id,
        confirmed_qty=Decimal('100'), # Changed from quantity
        unit_price=Decimal('10.30'), # Changed from price
        total_price=Decimal('1030.00') # Changed from amount
    )
    db_session.add(item1)
    db_session.commit()

    # Call Preview Service
    result = finance_service.preview_supply_contract_from_l1(l1.id)['data']
    
    aggregated = result['items'][0]
    assert aggregated['tax_rate'] == Decimal('0.03') # From Small Supplier
    assert aggregated['invoice_name'] == 'Test Declared Name'

def test_generate_supply_contract_api(client, token_headers, setup_l15_data, db_session):
    """测试 API 端点: 预览并生成"""
    data = setup_l15_data
    supplier = data['supplier_gen']
    product = data['product']

    # 1. Create L1
    l1 = ScmDeliveryContract(
        contract_no='L1-API-TEST',
        supplier_id=supplier.id,
        total_amount=Decimal('100.00'),
        currency='CNY'
    )
    db_session.add(l1)
    db_session.flush()
    item = ScmDeliveryContractItem(
        l1_contract_id=l1.id,
        product_id=product.id,
        confirmed_qty=Decimal('10'),
        unit_price=Decimal('10.00'),
        total_price=Decimal('100.00')
    )
    db_session.add(item)
    db_session.commit()

    # 2. Test Preview API
    resp = client.get(f'/api/v1/serc/finance/supply-contracts/preview/{l1.id}', headers=token_headers)
    assert resp.status_code == 200
    preview_data = resp.json['data']
    assert preview_data['l1_contract_id'] == l1.id
    assert preview_data['is_balanced'] is True
    
    items_to_confirm = preview_data['items']

    # 3. Test Generate API
    payload = {
        'l1_contract_id': l1.id,
        'confirmed_items': items_to_confirm
    }
    
    resp_gen = client.post('/api/v1/serc/finance/supply-contracts/generate', json=payload, headers=token_headers)
    assert resp_gen.status_code == 200
    assert resp_gen.json['data']['contract_no'] == 'L1-API-TEST'
    
    # 4. Verify DB
    contract = db.session.query(FinSupplyContract).filter_by(l1_contract_id=l1.id).first()
    assert contract is not None
    assert contract.status == 'draft'
    assert len(contract.items) == 1
    assert contract.items[0].tax_rate == Decimal('0.13')
