from apiflask import Schema
from apiflask.fields import Integer, String, Date, Dict, List, Decimal as DecimalField
from app.schemas.pagination import PaginationQuerySchema

class SupplierSearchSchema(PaginationQuerySchema):
    """供应商搜索 Schema"""
    supplier_type = String(load_default=None, metadata={'description': '供应商类型'})
    status = String(load_default=None, metadata={'description': '状态'})

class SupplierDetailSchema(Schema):
    """供应商详情 Schema"""
    id = Integer(metadata={'description': '供应商ID'})
    code = String(metadata={'description': '供应商代码'})
    name = String(metadata={'description': '供应商名称'})
    short_name = String(metadata={'description': '简称'})
    supplier_type = String(metadata={'description': '类型'})
    status = String(metadata={'description': '状态'})
    grade = String(metadata={'description': '等级'})
    
    # 地址
    country = String(metadata={'description': '国家'})
    province = String(metadata={'description': '省份'})
    city = String(metadata={'description': '城市'})
    address = String(metadata={'description': '详细地址'})
    website = String(metadata={'description': '官网'})
    
    # 联系人
    primary_contact = String(metadata={'description': '首要联系人'})
    primary_phone = String(metadata={'description': '联系电话'})
    primary_email = String(metadata={'description': 'Email'})
    contacts = List(Dict(), metadata={'description': '联系人列表'})
    
    # 财务
    tax_id = String(metadata={'description': '税号'})
    currency = String(metadata={'description': '币种'})
    payment_terms = String(attribute='payment_term_name', metadata={'description': '付款条款(智能显示)'})
    payment_term_id = Integer(metadata={'description': '付款条款ID'}) # Added
    payment_method = String(metadata={'description': '付款方式'})
    bank_accounts = List(Dict(), metadata={'description': '银行账户'})
    
    # 新增纳税人信息 (Detail)
    taxpayer_type = String(metadata={'description': '纳税人类型'})
    default_vat_rate = DecimalField(metadata={'description': '默认开票税率'})

    # 运营
    lead_time_days = Integer(metadata={'description': '交货天数'})
    moq = String(metadata={'description': 'MOQ'})
    
    # 管理
    purchase_uid = Integer(metadata={'description': '采购员ID'})
    notes = String(metadata={'description': '备注'})
    tags = List(String(), metadata={'description': '标签'})
    
    created_at = Date()
    updated_at = Date()

class SupplierSimpleSchema(Schema):
    """供应商列表 Schema (简化版)"""
    id = Integer()
    code = String()
    name = String()
    short_name = String()
    supplier_type = String()
    status = String()
    primary_contact = String()
    primary_phone = String()
    currency = String()
    grade = String()
    # Smart resolve
    payment_term_id = Integer()

class SupplierCreateSchema(Schema):
    """创建供应商 Schema"""
    code = String(required=False, load_default='', metadata={'description': '供应商代码 (留空自动生成)', 'example': 'SUP001'})
    name = String(required=True, metadata={'description': '供应商名称'})
    short_name = String()
    supplier_type = String(load_default='manufacturer')
    status = String(load_default='active')
    grade = String()
    
    country = String()
    province = String()
    city = String()
    address = String()
    website = String()
    
    primary_contact = String()
    primary_phone = String()
    primary_email = String()
    contacts = List(Dict())
    
    tax_id = String()
    currency = String(load_default='CNY')
    payment_terms = String()
    payment_term_id = Integer() # Added
    payment_method = String()
    bank_accounts = List(Dict())
    
    # 新增纳税人信息 (Create/Update)
    taxpayer_type = String(metadata={'description': '纳税人类型 (general, small)'})
    default_vat_rate = DecimalField(metadata={'description': '默认开票税率 (0.13, 0.03)'})

    lead_time_days = Integer()
    moq = String()
    
    purchase_uid = Integer()
    notes = String()
    tags = List(String())

class SupplierUpdateSchema(SupplierCreateSchema):
    """更新供应商 Schema"""
    code = String(required=False)
    name = String(required=False)
