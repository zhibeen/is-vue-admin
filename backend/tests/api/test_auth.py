import pytest
from tests.factories import UserFactory, RoleFactory, PermissionFactory

def test_login_success(client, db_session):
    """Test valid login returns token"""
    # 1. Create user via Factory
    user = UserFactory(username='tester', password='secure_password')
    
    # 2. Login
    response = client.post('/api/v1/auth/login', json={
        'username': 'tester',
        'password': 'secure_password'
    })
    
    assert response.status_code == 200
    data = response.json
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert data['username'] == 'tester'

def test_login_failed(client, db_session):
    """Test invalid login returns 401"""
    UserFactory(username='tester', password='password')
    
    response = client.post('/api/v1/auth/login', json={
        'username': 'tester',
        'password': 'wrong_password'
    })
    
    assert response.status_code == 401

def test_me_with_permissions(client, db_session):
    """Test /me returns correct permissions"""
    # 1. Setup RBAC
    perm1 = PermissionFactory(name='product:read')
    perm2 = PermissionFactory(name='product:write')
    
    role = RoleFactory(name='manager', permissions=[perm1, perm2])
    user = UserFactory(username='manager', roles=[role])
    
    # 2. Get Token
    login_resp = client.post('/api/v1/auth/login', json={
        'username': 'manager',
        'password': 'password'
    })
    token = login_resp.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 3. Call /me
    response = client.get('/api/v1/auth/me', headers=headers)
    
    assert response.status_code == 200
    data = response.json
    assert data['username'] == 'manager'
    assert 'manager' in data['roles']
    assert 'product:read' in data['permissions']
    assert 'product:write' in data['permissions']

