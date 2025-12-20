import factory
from app import db
from app.models.user import User, Role, Permission
from app.models.product import Product
from app.models.product import Category
from app.models.vehicle import VehicleAux
from app.models.purchase.supplier import SysSupplier
from app.models.supply.delivery import ScmDeliveryContract, ScmDeliveryContractItem, ScmSourceDoc
from app.models.serc.enums import ContractStatus, SourceDocType
from app.models.logistics.logistics_provider import LogisticsProvider
from app.models.logistics.shipment import ShipmentOrder
from app.models.logistics.shipment_logistics_service import ShipmentLogisticsService
from app.models.logistics.logistics_statement import LogisticsStatement
from app.models.serc.payable import FinPayable, FinPaymentPool
from decimal import Decimal
from datetime import date, datetime

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


# ==================== 物流相关 Factories ==================== #

class LogisticsProviderFactory(factory.alchemy.SQLAlchemyModelFactory):
    """物流服务商 Factory"""
    class Meta:
        model = LogisticsProvider
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    provider_name = factory.Sequence(lambda n: f'物流商_{n}')
    provider_code = factory.Sequence(lambda n: f'LP{n:03d}')
    service_type = 'express'
    payment_method = 'monthly'
    settlement_cycle = 'monthly'
    contact_name = factory.Faker('name')
    contact_phone = factory.Faker('phone_number')
    bank_name = '中国工商银行'
    bank_account = factory.Sequence(lambda n: f'6222{n:014d}')
    bank_account_name = factory.Sequence(lambda n: f'物流商_{n}')
    is_active = True


class ShipmentOrderFactory(factory.alchemy.SQLAlchemyModelFactory):
    """发货单 Factory"""
    class Meta:
        model = ShipmentOrder
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    shipment_no = factory.Sequence(lambda n: f'SH{datetime.now().strftime("%Y%m%d")}{n:04d}')
    source = 'manual'
    status = 'confirmed'
    shipper_company_id = 1  # 需要预先存在
    consignee_name = factory.Faker('name')
    consignee_address = factory.Faker('address')
    consignee_country = 'US'


class ShipmentLogisticsServiceFactory(factory.alchemy.SQLAlchemyModelFactory):
    """物流服务记录 Factory"""
    class Meta:
        model = ShipmentLogisticsService
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    shipment = factory.SubFactory(ShipmentOrderFactory)
    logistics_provider = factory.SubFactory(LogisticsProviderFactory)
    service_type = 'main_transport'
    service_description = '国际运输'
    estimated_amount = Decimal('1000.00')
    actual_amount = Decimal('1050.00')
    currency = 'CNY'
    status = 'confirmed'
    confirmed_at = factory.LazyFunction(datetime.now)


class LogisticsStatementFactory(factory.alchemy.SQLAlchemyModelFactory):
    """物流对账单 Factory"""
    class Meta:
        model = LogisticsStatement
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    statement_no = factory.Sequence(lambda n: f'LS{datetime.now().strftime("%Y%m%d")}{n:04d}')
    logistics_provider = factory.SubFactory(LogisticsProviderFactory)
    statement_period_start = factory.LazyFunction(lambda: date.today().replace(day=1))
    statement_period_end = factory.LazyFunction(date.today)
    total_amount = Decimal('5000.00')
    currency = 'CNY'
    status = 'draft'


# ==================== 财务相关 Factories ==================== #

class FinPayableFactory(factory.alchemy.SQLAlchemyModelFactory):
    """财务应付单 Factory"""
    class Meta:
        model = FinPayable
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    payable_no = factory.Sequence(lambda n: f'AP{datetime.now().strftime("%Y%m%d")}{n:04d}')
    source_type = 'logistics'
    source_id = 1
    source_no = factory.Sequence(lambda n: f'LS{datetime.now().strftime("%Y%m%d")}{n:04d}')
    payee_type = 'logistics_provider'
    payee_id = 1
    payee_name = '测试物流商'
    bank_name = '中国工商银行'
    bank_account = '6222000000000001'
    bank_account_name = '测试物流商'
    payable_amount = Decimal('5000.00')
    paid_amount = Decimal('0.00')
    currency = 'CNY'
    priority = 3
    status = 'pending'


class FinPaymentPoolFactory(factory.alchemy.SQLAlchemyModelFactory):
    """付款池 Factory"""
    class Meta:
        model = FinPaymentPool
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    pool_no = factory.Sequence(lambda n: f'PP{datetime.now().strftime("%Y%m")}{n:03d}')
    pool_name = factory.LazyFunction(lambda: f'{datetime.now().year}年{datetime.now().month}月付款池')
    scheduled_date = factory.LazyFunction(date.today)
    total_amount = Decimal('0.00')
    total_count = 0
    status = 'draft'
