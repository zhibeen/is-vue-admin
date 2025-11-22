import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, Role, Permission
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
import sqlalchemy.dialects.sqlite

# Monkey-patch JSONB for SQLite
sqlalchemy.dialects.sqlite.base.SQLiteDialect.supports_json = True
# Register JSONB to compile as JSON in SQLite
def compile_jsonb(type_, compiler, **kw):
    return "JSON"

sqlalchemy.dialects.sqlite.base.SQLiteTypeCompiler.visit_JSONB = compile_jsonb


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Use SQLite in-memory for fast testing
    # Set JWT_SECRET_KEY for consistent token generation
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret',
        'SECRET_KEY': 'test-secret'
    }
    
    app = create_app(config)
    
    # Create application context
    with app.app_context():
        db.create_all() # Create tables
        yield app
        db.session.remove()
        db.drop_all() # Drop tables

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()

@pytest.fixture
def db_session(app):
    """
    Creates a new database session for a test.
    (Not strictly necessary if using app.app_context() but good for factory_boy)
    """
    with app.app_context():
        yield db.session

@pytest.fixture
def admin_user(app):
    """Create an admin user with all permissions"""
    with app.app_context():
        # 1. Create Permissions
        perms = ['product:create', 'product:delete', 'vehicle:manage']
        perm_objs = []
        for p in perms:
            perm = Permission(name=p)
            db.session.add(perm)
            perm_objs.append(perm)
            
        # 2. Create Admin Role
        role = Role(name='admin')
        role.permissions = perm_objs
        db.session.add(role)
        
        # 3. Create User
        user = User(username='admin', email='admin@test.com')
        user.set_password('password')
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        
        # Re-fetch to attach to current session if needed
        return db.session.get(User, user.id)

@pytest.fixture
def token_headers(client, admin_user):
    """Get auth headers for the admin user"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'password'
    })
    token = response.json['access_token']
    return {
        'Authorization': f'Bearer {token}'
    }

