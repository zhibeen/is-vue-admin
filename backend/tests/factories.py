import factory
from app import db
from app.models.user import User, Role, Permission
from app.models.product import Product
from app.models.category import Category
from app.models.vehicle import VehicleAux

class PermissionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Permission
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'perm:{n}')
    description = factory.Faker('sentence')

class RoleFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Role
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'role_{n}')
    
    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for perm in extracted:
                self.permissions.append(perm)

from werkzeug.security import generate_password_hash

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Sequence(lambda n: f'user_{n}@example.com')
    
    # Transient field (not saved to DB)
    password = factory.Faker('password')
    
    # Generate hash from password immediately
    password_hash = factory.LazyAttribute(lambda o: generate_password_hash(o.password))
    
    is_active = True

    class Params:
        password = 'password' # Default value if not provided

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for role in extracted:
                self.roles.append(role)

class CategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Category
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
        
    name = factory.Sequence(lambda n: f'Category {n}')
    code = factory.Sequence(lambda n: f'CAT{n}')

class VehicleAuxFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = VehicleAux
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
        
    name = factory.Faker('word')
    level_type = 'brand'
    code = factory.Sequence(lambda n: f'V{n}')

