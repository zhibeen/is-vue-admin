import pytest
from tests.factories import UserFactory, RoleFactory, PermissionFactory, CategoryFactory

def test_create_product_permission_denied(client, db_session):
    """
    Test that a user WITHOUT 'product:create' permission 
    CANNOT create a product (Should return 403).
    """
    # 1. Create a regular user (no permissions)
    user = UserFactory(username='guest', password='password')
    
    # 2. Get Token
    login_resp = client.post('/api/v1/auth/login', json={
        'username': 'guest',
        'password': 'password'
    })
    token = login_resp.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 3. Attempt to create product
    response = client.post('/api/v1/products', json={
        'name': 'Hacker Item',
        'category_id': 1
    }, headers=headers)
    
    # 4. Verify Access Denied
    assert response.status_code == 403
    assert 'Insufficient permissions' in response.json['message']

def test_create_product_permission_granted(client, db_session):
    """
    Test that a user WITH 'product:create' permission 
    CAN create a product (Should return 201).
    """
    # 1. Create authorized user
    perm = PermissionFactory(name='product:create')
    role = RoleFactory(name='creator', permissions=[perm])
    user = UserFactory(username='creator', roles=[role])
    
    # 2. Create Category (Dependency)
    category = CategoryFactory()
    
    # 3. Get Token
    login_resp = client.post('/api/v1/auth/login', json={
        'username': 'creator',
        'password': 'password'
    })
    headers = {'Authorization': f'Bearer {login_resp.json["access_token"]}'}
    
    # 4. Create Product
    payload = {
        'name': 'Legit Item',
        'category_id': category.id,
        'attributes': {'color': 'red'}
    }
    response = client.post('/api/v1/products', json=payload, headers=headers)
    
    assert response.status_code == 201
    assert response.json['name'] == 'Legit Item'

