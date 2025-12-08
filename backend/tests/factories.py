import factory
from app import db
from app.models.user import User, Role, Permission
from app.models.product import Product
from app.models.product import Category
from app.models.vehicle import VehicleAux
from app.models.purchase.supplier import SysSupplier
from app.models.supply.delivery import ScmDeliveryContract, ScmDeliveryContractItem, ScmSourceDoc
from app.models.serc.enums import ContractStatus, SourceDocType

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

# --- SERC Factories ---

class SysSupplierFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = SysSupplier
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    code = factory.Sequence(lambda n: f'SUP-{n:03d}')
    name = factory.Sequence(lambda n: f'Supplier_{n}')
    short_name = factory.Sequence(lambda n: f'SUP_{n}')
    supplier_type = 'manufacturer'
    status = 'active'
    currency = 'CNY'
    contacts = []
    bank_accounts = []
    tags = []

class ProductFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Product
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'Product_{n}')
    sku = factory.Sequence(lambda n: f'SKU-{n}')
    category = factory.SubFactory(CategoryFactory)

class ScmSourceDocFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ScmSourceDoc
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    doc_no = factory.Sequence(lambda n: f'VGRN-{n}')
    type = SourceDocType.GRN_STOCK.value
    event_date = factory.Faker('date_object')
    supplier = factory.SubFactory(SysSupplierFactory)

class ScmDeliveryContractFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ScmDeliveryContract
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    contract_no = factory.Sequence(lambda n: f'L1-{n}')
    supplier = factory.SubFactory(SysSupplierFactory)
    source_doc = factory.SubFactory(ScmSourceDocFactory)
    status = ContractStatus.PENDING.value
    total_amount = 0

class ScmDeliveryContractItemFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ScmDeliveryContractItem
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    contract = factory.SubFactory(ScmDeliveryContractFactory)
    product = factory.SubFactory(ProductFactory)
    confirmed_qty = 10
    unit_price = 100
    total_price = 1000
