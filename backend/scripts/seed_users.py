import logging
from app.extensions import db
from app.models.user import User, Role
from app.security import hash_password

logger = logging.getLogger(__name__)

def seed_users():
    logger.info("Initializing Users and Roles...")
    
    # 1. Create Roles
    admin_role = db.session.query(Role).filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator')
        db.session.add(admin_role)
        logger.info("Created role: admin")
    
    user_role = db.session.query(Role).filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user', description='Standard User')
        db.session.add(user_role)
        logger.info("Created role: user")
    
    db.session.flush()
    
    # 2. Create Users
    # Admin User
    admin = db.session.query(User).filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=hash_password('password'),
            is_active=True
        )
        admin.roles.append(admin_role)
        db.session.add(admin)
        logger.info("Created user: admin / password")
    
    # Standard User
    user = db.session.query(User).filter_by(username='user').first()
    if not user:
        user = User(
            username='user',
            email='user@example.com',
            password_hash=hash_password('password'),
            is_active=True
        )
        user.roles.append(user_role)
        db.session.add(user)
        logger.info("Created user: user / password")
        
    db.session.commit()
    logger.info("User initialization completed.")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_users()

