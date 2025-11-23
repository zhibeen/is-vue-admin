import pytest
from app.models.user import Permission

def test_permission_seed_data(app, db_session, admin_user):
    """Test that new view permissions are seeded correctly"""
    # admin_user fixture ensures permissions are created in the db session
    with app.app_context():
        # Verify System View Permission
        sys_view = db_session.scalar(db_session.query(Permission).where(Permission.name == 'system:view'))
        # Note: description might vary depending on seed/conftest, checking existence is key
        assert sys_view is not None 

        # Verify Product View Permission
        prod_view = db_session.scalar(db_session.query(Permission).where(Permission.name == 'product:view'))
        assert prod_view is not None

def test_get_permission_tree(client, admin_user, token_headers):
    """Test the structured permission tree API"""
    
    # 1. Request the tree API
    response = client.get('/api/v1/system/permissions/tree', headers=token_headers)
    assert response.status_code == 200
    
    data = response.json['data']
    assert isinstance(data, list)
    
    # 2. Verify Structure: Check for '商品中心' (Module)
    product_module = next((m for m in data if m['name'] == '商品中心'), None)
    assert product_module is not None
    assert product_module['label'] == '商品中心'
    
    # 3. Verify Children: Check for '商品列表' (Resource)
    product_resource = next((r for r in product_module['children'] if r['name'] == '商品列表'), None)
    assert product_resource is not None
    assert product_resource['label'] == '商品列表'
    
    # 4. Verify Permissions: Check for 'view' and 'create' actions
    perms = product_resource['permissions']
    view_perm = next((p for p in perms if p['code'] == 'product:view'), None)
    create_perm = next((p for p in perms if p['code'] == 'product:create'), None)
    
    assert view_perm is not None
    assert view_perm['label'] == '查看' # Should be mapped from ACTION_MAP
    
    assert create_perm is not None
    assert create_perm['label'] == '创建'

def test_permission_tree_chinese_mapping(client, admin_user, token_headers):
    """Test that keys are correctly mapped (now they ARE Chinese)"""
    response = client.get('/api/v1/system/permissions/tree', headers=token_headers)
    data = response.json['data']
    
    # Check System Module
    system_module = next((m for m in data if m['name'] == '系统管理'), None)
    assert system_module is not None
    
    # Check Role Management Sub-module
    role_res = next((r for r in system_module['children'] if r['name'] == '角色管理'), None)
    assert role_res is not None

