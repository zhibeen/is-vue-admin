import pytest
from app.models.user import Role, Permission

def test_create_role(client, admin_user, token_headers, db_session):
    """Test creating a new role with permissions"""
    # 1. Get some permission IDs
    perms = db_session.query(Permission).limit(2).all()
    perm_ids = [p.id for p in perms]
    
    # 2. Create Role
    data = {
        'name': 'test_role_manager',
        'description': 'Test Role Description',
        'permission_ids': perm_ids
    }
    
    response = client.post('/api/v1/system/roles', json=data, headers=token_headers)
    assert response.status_code == 201
    assert response.json['data']['name'] == 'test_role_manager'
    assert len(response.json['data']['permissions']) == 2

def test_get_roles_list(client, admin_user, token_headers):
    """Test getting role list"""
    response = client.get('/api/v1/system/roles', headers=token_headers)
    assert response.status_code == 200
    data = response.json['data']
    assert len(data) >= 1 # At least admin role
    # Verify permissions are nested
    assert 'permissions' in data[0]

def test_update_role(client, admin_user, token_headers, db_session):
    """Test updating a role"""
    # Create a temp role first
    role = Role(name='temp_role')
    db_session.add(role)
    db_session.commit()
    
    data = {'name': 'updated_role_name'}
    response = client.put(f'/api/v1/system/roles/{role.id}', json=data, headers=token_headers)
    
    assert response.status_code == 200
    assert response.json['data']['name'] == 'updated_role_name'

def test_delete_role(client, admin_user, token_headers, db_session):
    """Test deleting a role"""
    role = Role(name='role_to_delete')
    db_session.add(role)
    db_session.commit()
    
    role_id = role.id # Store ID before delete
    response = client.delete(f'/api/v1/system/roles/{role_id}', headers=token_headers)
    # 2025-11-27 Fix: API returns 200 OK with null data, not 204 No Content
    # Reference: BaseResponse schema behavior
    assert response.status_code == 200
    
    # Verify deletion
    # Need to expire/refresh session or query anew
    db_session.expire_all()
    assert db_session.get(Role, role_id) is None
