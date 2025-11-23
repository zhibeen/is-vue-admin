import pytest
from sqlalchemy import select
from app.models.data_permission import DataPermissionMeta, RoleDataPermission
from app.models.user import Role
from app.extensions import db

# Initialize Metas Helper
def init_metas(db_session):
    # Create simple L1 -> L2 -> L3 structure
    # L1
    l1 = DataPermissionMeta(key='test_cat', label='Test Category', type='category', sort_order=1)
    db_session.add(l1)
    db_session.flush()
    
    # L2
    l2 = DataPermissionMeta(key='test_cat:mod', label='Test Module', type='module', parent_id=l1.id)
    db_session.add(l2)
    db_session.flush()
    
    # L3
    l3 = DataPermissionMeta(key='test_cat:mod:res', label='Test Resource', type='resource', parent_id=l2.id)
    db_session.add(l3)
    db_session.commit()
    return l1, l2, l3

class TestDataPermission:
    
    def test_get_metas_structure(self, client, token_headers, db_session):
        """Test fetching the meta tree structure"""
        # Setup
        init_metas(db_session)
        
        # Execute
        response = client.get('/api/v1/system/data-permission-metas', headers=token_headers)
        
        # Verify
        assert response.status_code == 200
        data = response.json['data']
        assert len(data) >= 1
        
        # Find our test node
        root = next((n for n in data if n['key'] == 'test_cat'), None)
        assert root is not None
        assert root['label'] == 'Test Category'
        assert len(root['children']) == 1
        
        module = root['children'][0]
        assert module['key'] == 'test_cat:mod'
        assert len(module['children']) == 1
        
        resource = module['children'][0]
        assert resource['key'] == 'test_cat:mod:res'

    def test_get_role_config_default(self, client, token_headers, db_session, admin_user):
        """Test getting config when none exists (should return empty defaults)"""
        # Setup
        # Re-attach user to session
        user = db_session.merge(admin_user)
        role_id = user.roles[0].id
        
        # Execute
        response = client.get(
            f'/api/v1/system/roles/{role_id}/data-permissions?category_key=test_cat', 
            headers=token_headers
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json['data']
        assert data['category_key'] == 'test_cat'
        assert data['target_user_ids'] == []
        assert data['resource_scopes'] == {}

    def test_save_and_get_role_config(self, client, token_headers, db_session, admin_user):
        """Test saving configuration and retrieving it"""
        # Setup
        user = db_session.merge(admin_user)
        role_id = user.roles[0].id
        
        payload = {
            'category_key': 'test_cat',
            'target_user_ids': [1, 2, 3],
            'resource_scopes': {
                'test_cat:mod:res': 'custom',
                'test_cat:mod:other': 'all'
            }
        }
        
        # Execute Save
        response = client.post(
            f'/api/v1/system/roles/{role_id}/data-permissions', 
            json=payload,
            headers=token_headers
        )
        
        # Verify Save Response
        assert response.status_code == 200
        
        # Execute Get
        response = client.get(
            f'/api/v1/system/roles/{role_id}/data-permissions?category_key=test_cat', 
            headers=token_headers
        )
        
        # Verify Get
        assert response.status_code == 200
        data = response.json['data']
        assert data['category_key'] == 'test_cat'
        assert set(data['target_user_ids']) == {1, 2, 3}
        assert data['resource_scopes']['test_cat:mod:res'] == 'custom'
        assert data['resource_scopes']['test_cat:mod:other'] == 'all'

    def test_update_role_config(self, client, token_headers, db_session, admin_user):
        """Test updating existing configuration"""
        # Setup - Create initial config
        user = db_session.merge(admin_user)
        role_id = user.roles[0].id
        
        config = RoleDataPermission(
            role_id=role_id,
            category_key='test_cat',
            target_user_ids=[1],
            resource_scopes={'k': 'v'}
        )
        db_session.add(config)
        db_session.commit()
        
        # Update payload
        payload = {
            'category_key': 'test_cat',
            'target_user_ids': [99],
            'resource_scopes': {'k': 'v2'}
        }
        
        # Execute
        client.post(
            f'/api/v1/system/roles/{role_id}/data-permissions', 
            json=payload,
            headers=token_headers
        )
        
        # Verify
        new_config = db_session.scalar(select(RoleDataPermission).where(RoleDataPermission.role_id == role_id))
        assert new_config.target_user_ids == [99]
        assert new_config.resource_scopes == {'k': 'v2'}

