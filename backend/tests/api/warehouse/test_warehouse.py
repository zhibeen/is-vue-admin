import pytest
from app.models.warehouse.warehouse import Warehouse, WarehouseLocation
from app.models.user import Permission

@pytest.fixture
def warehouse_admin(client, admin_user, db_session):
    """Add warehouse permissions to admin user"""
    # Check if permission already exists to avoid unique constraint error if run multiple times in same session logic
    perms = ['warehouse:view', 'warehouse:create', 'warehouse:update', 'warehouse:delete']
    
    # Reload admin_user to ensure it's attached to the current session
    # admin_user = db_session.merge(admin_user) 
    # Actually admin_user fixture returns a detached object sometimes or session might be different?
    # conftest.py says: return db.session.get(User, user.id)
    
    for p_name in perms:
        existing = db_session.query(Permission).filter_by(name=p_name).first()
        if not existing:
            p = Permission(name=p_name, description=p_name, module='仓库', resource='仓', action='all')
            db_session.add(p)
            admin_user.roles[0].permissions.append(p)
        else:
            if existing not in admin_user.roles[0].permissions:
                admin_user.roles[0].permissions.append(existing)
    
    db_session.commit()
    return admin_user

def test_get_warehouse_list(client, token_headers, warehouse_admin, db_session):
    """测试获取仓库列表"""
    # Clean up first (optional, depends on isolation)
    db_session.query(Warehouse).delete()
    
    # Create mock data
    w1 = Warehouse(code='W1', name='Warehouse 1', category='physical', location_type='domestic', ownership_type='self')
    w2 = Warehouse(code='W2', name='Warehouse 2', category='virtual', location_type='domestic', ownership_type='self')
    db_session.add_all([w1, w2])
    db_session.commit()
    
    resp = client.get('/api/v1/warehouses', headers=token_headers)
    assert resp.status_code == 200, f"Response: {resp.data}"
    
    data = resp.json['data']
    assert data['total'] == 2
    codes = [item['code'] for item in data['items']]
    assert 'W1' in codes
    assert 'W2' in codes

def test_create_warehouse(client, token_headers, warehouse_admin, db_session):
    """测试创建仓库"""
    payload = {
        'code': 'NEW-WH',
        'name': 'New Warehouse',
        'category': 'physical',
        'location_type': 'domestic',
        'ownership_type': 'self',
        'business_type': 'standard',
        'currency': 'CNY'
    }
    resp = client.post('/api/v1/warehouses', json=payload, headers=token_headers)
    assert resp.status_code == 201
    assert resp.json['data']['code'] == 'NEW-WH'
    
    # Verify DB
    wh = db_session.query(Warehouse).filter_by(code='NEW-WH').first()
    assert wh is not None
    assert wh.name == 'New Warehouse'

def test_update_warehouse(client, token_headers, warehouse_admin, db_session):
    """测试更新仓库"""
    w = Warehouse(code='UPD-WH', name='Original Name', category='physical', location_type='domestic', ownership_type='self')
    db_session.add(w)
    db_session.commit()
    
    payload = {'name': 'Updated Name'}
    resp = client.put(f'/api/v1/warehouses/{w.id}', json=payload, headers=token_headers)
    assert resp.status_code == 200
    assert resp.json['data']['name'] == 'Updated Name'

def test_delete_warehouse(client, token_headers, warehouse_admin, db_session):
    """测试删除仓库"""
    w = Warehouse(code='DEL-WH', name='Delete Me', category='physical', location_type='domestic', ownership_type='self')
    db_session.add(w)
    db_session.commit()
    
    resp = client.delete(f'/api/v1/warehouses/{w.id}', headers=token_headers)
    assert resp.status_code == 200
    
    wh = db_session.get(Warehouse, w.id)
    assert wh is None

def test_warehouse_locations(client, token_headers, warehouse_admin, db_session):
    """测试库位增删改查"""
    w = Warehouse(code='LOC-WH', name='Loc Warehouse', category='physical', location_type='domestic', ownership_type='self')
    db_session.add(w)
    db_session.commit()
    
    # 1. Create Location
    payload = {
        'code': 'A-01-01',
        'type': 'storage',
        'is_locked': False
    }
    resp = client.post(f'/api/v1/warehouses/{w.id}/locations', json=payload, headers=token_headers)
    assert resp.status_code == 201
    loc_id = resp.json['data']['id']
    
    # 2. Get List
    resp = client.get(f'/api/v1/warehouses/{w.id}/locations', headers=token_headers)
    assert resp.status_code == 200
    assert resp.json['data']['total'] == 1
    
    # 3. Update
    resp = client.put(f'/api/v1/warehouses/locations/{loc_id}', json={'is_locked': True}, headers=token_headers)
    assert resp.status_code == 200
    assert resp.json['data']['is_locked'] is True
    
    # 4. Delete
    resp = client.delete(f'/api/v1/warehouses/locations/{loc_id}', headers=token_headers)
    assert resp.status_code == 200
    assert db_session.get(WarehouseLocation, loc_id) is None

