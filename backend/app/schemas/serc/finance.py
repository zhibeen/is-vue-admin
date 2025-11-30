from apiflask import Schema
from apiflask.fields import Integer, String, Decimal, List, Date, Nested
from marshmallow import validate

# --- L2 SOA Schemas ---

class SOAGenerateSchema(Schema):
    # 提交 L1 ID 列表生成 L2
    l1_ids = List(Integer(), required=True, validate=validate.Length(min=1), metadata={'description': 'L1合同ID列表'})

class SOADetailItemSchema(Schema):
    id = Integer()
    l1_contract_id = Integer()
    l1_contract_no = String(attribute='l1_contract.contract_no')
    amount = Decimal(places=2)
    allocated_payment = Decimal(places=2)

class SOAItemSchema(Schema):
    id = Integer()
    soa_no = String()
    supplier_id = Integer()
    supplier_name = String(attribute='supplier.name')
    total_payable = Decimal(places=2)
    paid_amount = Decimal(places=2)
    invoiced_amount = Decimal(places=2)
    payment_status = String()
    invoice_status = String()
    created_at = Date()
    
    details = List(Nested(SOADetailItemSchema))

class SOASearchSchema(Schema):
    page = Integer(load_default=1)
    per_page = Integer(load_default=20)
    soa_no = String(required=False)
    supplier_id = Integer(required=False)
    payment_status = String(required=False)

# --- Payment Pool Schemas ---

class PaymentPoolItemSchema(Schema):
    id = Integer()
    soa_id = Integer()
    soa_no = String(attribute='soa.soa_no')
    amount = Decimal(places=2)
    type = String()
    status = String()
    priority = Integer()

class PaymentCreateSchema(Schema):
    # 提交 Pool Item ID 列表生成 L3
    pool_item_ids = List(Integer(), required=True, validate=validate.Length(min=1))
    bank_account = String(required=True)

class PaymentRequestSchema(Schema):
    id = Integer()
    request_no = String()
    total_pay_amount = Decimal(places=2)
    bank_account = String()
    created_at = Date()
