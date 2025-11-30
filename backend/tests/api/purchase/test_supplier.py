import pytest
from app.models.purchase.supplier import SysSupplier
from tests.factories import SysSupplierFactory

def test_create_supplier_full(client, token_headers):
    """Test creating a supplier with full details including JSONB fields"""
    payload = {
        "code": "SUP-FULL-001",
        "name": "Full Feature Supplier",
        "short_name": "FFS",
        "supplier_type": "manufacturer",
        "status": "active",
        "grade": "A",
        "country": "China",
        "province": "Guangdong",
        "city": "Shenzhen",
        "address": "Tech Park",
        "website": "https://example.com",
        "primary_contact": "Alice",
        "primary_phone": "13800000001",
        "primary_email": "alice@example.com",
        "contacts": [
            {"name": "Bob", "role": "Sales", "phone": "13900000002"},
            {"name": "Charlie", "role": "Finance", "email": "finance@example.com"}
        ],
        "tax_id": "91440300XXXXXXXXXX",
        "currency": "USD",
        "payment_terms": "Net 60",
        "payment_method": "T/T",
        "bank_accounts": [
            {
                "bank_name": "HSBC",
                "account": "123-456-789",
                "currency": "USD",
                "swift": "HSBCHKHH"
            },
            {
                "bank_name": "ICBC",
                "account": "622202XXXXXXXXXXXX",
                "currency": "CNY",
                "purpose": "Basic"
            }
        ],
        "lead_time_days": 14,
        "moq": "100 PCS",
        "notes": "Strategic partner",
        "tags": ["strategic", "electronics"]
    }
    
    # Update path: /api/v1/purchase/suppliers
    response = client.post('/api/v1/purchase/suppliers', 
                          json=payload, 
                          headers=token_headers)
    
    assert response.status_code == 201
    data = response.json['data']
    
    # Verify basic fields
    assert data['code'] == "SUP-FULL-001"
    assert data['name'] == "Full Feature Supplier"
    assert data['grade'] == "A"
    
    # Verify JSONB fields
    assert len(data['contacts']) == 2
    assert data['contacts'][0]['name'] == "Bob"
    assert len(data['bank_accounts']) == 2
    assert data['bank_accounts'][0]['bank_name'] == "HSBC"
    assert data['tags'] == ["strategic", "electronics"]

def test_get_supplier_list(client, token_headers):
    """Test listing suppliers"""
    # Create via factory
    s1 = SysSupplierFactory(name="List Sup 1", code="L001", supplier_type="trader")
    s2 = SysSupplierFactory(name="List Sup 2", code="L002", supplier_type="manufacturer")
    
    response = client.get('/api/v1/purchase/suppliers', headers=token_headers)
    
    assert response.status_code == 200
    # Fix: pagination returns {'data': {'items': [...], 'total': ...}}
    # So response.json['data'] is the pagination object.
    data = response.json['data']['items']
    
    # Filter to find our created ones (db might have seed data)
    found_s1 = next((item for item in data if item['code'] == 'L001'), None)
    found_s2 = next((item for item in data if item['code'] == 'L002'), None)
    
    assert found_s1 is not None
    assert found_s1['supplier_type'] == "trader"
    assert found_s2 is not None
    assert found_s2['supplier_type'] == "manufacturer"

def test_get_supplier_detail(client, token_headers):
    """Test getting single supplier detail"""
    supplier = SysSupplierFactory(
        name="Detail Sup",
        code="D001",
        contacts=[{"name": "Test Contact"}],
        bank_accounts=[{"bank": "Test Bank"}]
    )
    
    response = client.get(f'/api/v1/purchase/suppliers/{supplier.id}', headers=token_headers)
    
    assert response.status_code == 200
    data = response.json['data']
    assert data['name'] == "Detail Sup"
    assert data['contacts'] == [{"name": "Test Contact"}]
    assert data['bank_accounts'] == [{"bank": "Test Bank"}]

def test_update_supplier(client, token_headers):
    """Test updating supplier"""
    supplier = SysSupplierFactory(name="Old Name", code="U001", status="active")
    
    payload = {
        "name": "Updated Name",
        "status": "blacklisted",
        "tags": ["bad_quality"]
    }
    
    response = client.put(f'/api/v1/purchase/suppliers/{supplier.id}',
                         json=payload,
                         headers=token_headers)
    
    assert response.status_code == 200
    data = response.json['data']
    assert data['name'] == "Updated Name"
    assert data['status'] == "blacklisted"
    assert data['tags'] == ["bad_quality"]
    # Code should not change if not provided (or stay same)
    assert data['code'] == "U001"

def test_delete_supplier(client, token_headers):
    """Test deleting supplier"""
    supplier = SysSupplierFactory(name="Delete Me", code="DEL001")
    sid = supplier.id
    
    response = client.delete(f'/api/v1/purchase/suppliers/{sid}', headers=token_headers)
    assert response.status_code == 204
    
    # Verify it's gone
    response = client.get(f'/api/v1/purchase/suppliers/{sid}', headers=token_headers)
    assert response.status_code == 404
