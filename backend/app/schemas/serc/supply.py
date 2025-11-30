from apiflask import Schema
from apiflask.fields import Integer, String, Decimal, List, Date, Nested, Dict
from marshmallow import validate

# --- Shared Item Schema ---
class ScmDeliveryContractItemSchema(Schema):
    product_id = Integer(required=True, metadata={'description': '商品ID'})
    confirmed_qty = Decimal(required=True, places=4, metadata={'description': '确权数量'})
    unit_price = Decimal(required=True, places=4, metadata={'description': '含税单价'})
    notes = String(load_default='', metadata={'description': '备注'})
    
    # Read-only (calculated)
    total_price = Decimal(dump_only=True, places=2, metadata={'description': '总价'})
    product_name = String(dump_only=True, metadata={'description': '商品名称'})

# --- L1 Delivery Contract Schemas ---

class DeliveryContractCreateSchema(Schema):
    supplier_id = Integer(required=True, metadata={'description': '供应商ID'})
    company_id = Integer(required=True, metadata={'description': '采购主体ID'}) 
    currency = String(load_default='CNY', validate=validate.OneOf(['CNY', 'USD']), metadata={'description': '币种'})
    event_date = Date(required=True, metadata={'description': '业务日期'})

    # Added fields
    delivery_address = String(required=False, load_default='', metadata={'description': '交付地点'})
    delivery_date = Date(required=False, allow_none=True, metadata={'description': '送货日期'})
    notes = String(required=False, load_default='', metadata={'description': '合同备注'})

    # 新增可选字段
    payment_term_id = Integer(load_default=None, metadata={'description': '付款条款ID(结构化)'})
    payment_terms = String(load_default=None, metadata={'description': '付款条款(备注/快照)'})
    payment_method = String(load_default=None, metadata={'description': '付款方式(覆盖供应商默认)'})
    
    # Items
    items = List(Nested(ScmDeliveryContractItemSchema), required=True, validate=validate.Length(min=1))

class DeliveryContractDetailSchema(Schema):
    id = Integer()
    contract_no = String()
    
    supplier_id = Integer()
    supplier_name = String(attribute='supplier.name')
    
    company_id = Integer()
    company_name = String(attribute='company.short_name')
    
    total_amount = Decimal(places=2)
    paid_amount = Decimal(places=2, metadata={'description': '已付金额'})
    status = String()
    created_at = Date()
    event_date = Date(attribute='source_doc.event_date', metadata={'description': '业务日期'})
    
    # Added fields
    delivery_address = String()
    delivery_date = Date()
    notes = String()

    # 新增返回字段
    payment_term_id = Integer(metadata={'description': '付款条款ID'})
    payment_terms = String(metadata={'description': '付款条款(名称)'})
    payment_method = String(metadata={'description': '付款方式'})
    
    items = List(Nested(ScmDeliveryContractItemSchema))

class DeliveryContractSearchSchema(Schema):
    page = Integer(load_default=1)
    per_page = Integer(load_default=20)
    contract_no = String(required=False)
    supplier_id = Integer(required=False)
    company_id = Integer(required=False)
    status = String(required=False)

# --- Pagination Schema ---
class DeliveryContractPaginationSchema(Schema):
    items = List(Nested(DeliveryContractDetailSchema), metadata={'description': '数据列表'})
    total = Integer(metadata={'description': '总记录数'})
    pages = Integer(metadata={'description': '总页数'})
    page = Integer(metadata={'description': '当前页'})
    per_page = Integer(metadata={'description': '每页数量'})
