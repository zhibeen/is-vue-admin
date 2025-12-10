from apiflask import Schema
from apiflask.fields import Integer, String, Decimal, Date, Dict, List, Float

class CompanySimpleSchema(Schema):
    """公司列表展示Schema"""
    id = Integer(metadata={'description': '公司ID'})
    legal_name = String(metadata={'description': '法定名称'})
    short_name = String(metadata={'description': '简称'})
    english_name = String(metadata={'description': '英文名称'})
    unified_social_credit_code = String(metadata={'description': '统一社会信用代码'})
    tax_id = String(metadata={'description': '纳税人识别号'})
    status = String(metadata={'description': '状态'})
    contact_person = String(metadata={'description': '联系人'})
    contact_phone = String(metadata={'description': '联系电话'})
    created_at = Date(metadata={'description': '创建时间'})

class CompanyDetailSchema(Schema):
    """公司详情Schema"""
    id = Integer(metadata={'description': '公司ID'})
    
    # 基础信息
    legal_name = String(metadata={'description': '法定名称'})
    short_name = String(metadata={'description': '简称'})
    english_name = String(metadata={'description': '英文名称'})
    company_type = String(metadata={'description': '公司类型'})
    status = String(metadata={'description': '状态'})
    
    # 证照信息
    unified_social_credit_code = String(metadata={'description': '统一社会信用代码 (五证合一)'})
    tax_id = String(metadata={'description': '纳税人识别号 (已废弃，请使用统一社会信用代码)', 'deprecated': True})
    business_license_no = String(metadata={'description': '营业执照注册号 (已废弃，请使用统一社会信用代码)', 'deprecated': True})
    business_license_issue_date = Date(metadata={'description': '营业执照发证日期'})
    business_license_expiry_date = Date(metadata={'description': '营业执照有效期'})
    business_scope = String(metadata={'description': '经营范围'})
    
    # 地址信息
    registered_address = String(metadata={'description': '注册地址'})
    business_address = String(metadata={'description': '经营地址'})
    postal_code = String(metadata={'description': '邮政编码'})
    
    # 联系信息
    contact_person = String(metadata={'description': '联系人'})
    contact_phone = String(metadata={'description': '联系电话'})
    contact_email = String(metadata={'description': '联系邮箱'})
    fax = String(metadata={'description': '传真'})
    
    # 财务信息
    bank_accounts = List(Dict(), metadata={'description': '银行账户列表'})
    tax_rate = Float(metadata={'description': '增值税率'})
    tax_registration_date = Date(metadata={'description': '税务登记日期'})
    
    # 跨境业务
    customs_code = String(metadata={'description': '海关编码 (CR Code)'})
    customs_registration_no = String(metadata={'description': '海关注册登记编号 (已废弃)', 'deprecated': True})
    inspection_code = String(metadata={'description': '检验检疫代码 (已废弃)', 'deprecated': True})
    foreign_trade_operator_code = String(metadata={'description': '对外贸易经营者备案号'})
    forex_account = String(metadata={'description': '外汇账户 (已移动至银行账户)', 'deprecated': True})
    forex_registration_no = String(metadata={'description': '外汇登记证号 (已废弃)', 'deprecated': True})
    
    # 资质证照
    import_export_license_no = String(metadata={'description': '进出口许可证号 (已废弃，一般贸易无需)', 'deprecated': True})
    import_export_license_expiry = Date(metadata={'description': '进出口许可证有效期 (已废弃)', 'deprecated': True})
    special_licenses = List(Dict(), metadata={'description': '特殊资质列表'})
    
    # 业务配置
    default_currency = String(metadata={'description': '默认币种'})
    default_payment_term = String(metadata={'description': '默认付款条款'})
    credit_limit = Decimal(places=2, metadata={'description': '信用额度'})
    settlement_cycle = Integer(metadata={'description': '结算周期（天）'})
    cross_border_platform_ids = Dict(metadata={'description': '跨境平台账号'})
    
    # 附件与备注
    attachments = List(Dict(), metadata={'description': '附件列表'})
    notes = String(metadata={'description': '备注'})
    
    # 审计字段
    created_by = Integer(metadata={'description': '创建人ID'})
    updated_by = Integer(metadata={'description': '更新人ID'})
    created_at = Date(metadata={'description': '创建时间'})
    updated_at = Date(metadata={'description': '更新时间'})

class CompanyCreateSchema(Schema):
    """创建公司Schema"""
    # 基础信息
    legal_name = String(required=True, metadata={'description': '法定名称', 'example': '深圳市XX科技有限公司'})
    short_name = String(metadata={'description': '简称', 'example': 'XX科技'})
    english_name = String(metadata={'description': '英文名称', 'example': 'XX Technology Co., Ltd.'})
    company_type = String(metadata={'description': '公司类型', 'example': '一般纳税人'})
    status = String(metadata={'description': '状态', 'example': 'active'})
    
    # 证照信息
    unified_social_credit_code = String(metadata={'description': '统一社会信用代码 (五证合一)', 'example': '91440300XXXXXXXXXX'})
    tax_id = String(metadata={'description': '纳税人识别号 (已废弃)', 'deprecated': True})
    business_license_no = String(metadata={'description': '营业执照注册号 (已废弃)', 'deprecated': True})
    business_license_issue_date = Date(metadata={'description': '营业执照发证日期'})
    business_license_expiry_date = Date(metadata={'description': '营业执照有效期'})
    business_scope = String(metadata={'description': '经营范围'})
    
    # 地址信息
    registered_address = String(metadata={'description': '注册地址'})
    business_address = String(metadata={'description': '经营地址'})
    postal_code = String(metadata={'description': '邮政编码'})
    
    # 联系信息
    contact_person = String(metadata={'description': '联系人'})
    contact_phone = String(metadata={'description': '联系电话'})
    contact_email = String(metadata={'description': '联系邮箱'})
    fax = String(metadata={'description': '传真'})
    
    # 财务信息
    bank_accounts = List(Dict(), metadata={'description': '银行账户列表'})
    tax_rate = Float(metadata={'description': '增值税率', 'example': 0.13})
    tax_registration_date = Date(metadata={'description': '税务登记日期'})
    
    # 跨境业务
    customs_code = String(metadata={'description': '海关编码 (CR Code)'})
    customs_registration_no = String(metadata={'description': '海关注册登记编号 (已废弃)', 'deprecated': True})
    inspection_code = String(metadata={'description': '检验检疫代码 (已废弃)', 'deprecated': True})
    foreign_trade_operator_code = String(metadata={'description': '对外贸易经营者备案号'})
    forex_account = String(metadata={'description': '外汇账户 (已移动至银行账户)', 'deprecated': True})
    forex_registration_no = String(metadata={'description': '外汇登记证号 (已废弃)', 'deprecated': True})
    
    # 资质证照
    import_export_license_no = String(metadata={'description': '进出口许可证号 (已废弃，一般贸易无需)', 'deprecated': True})
    import_export_license_expiry = Date(metadata={'description': '进出口许可证有效期 (已废弃)', 'deprecated': True})
    special_licenses = List(Dict(), metadata={'description': '特殊资质列表'})
    
    # 业务配置
    default_currency = String(metadata={'description': '默认币种', 'example': 'CNY'})
    default_payment_term = String(metadata={'description': '默认付款条款'})
    credit_limit = Decimal(places=2, metadata={'description': '信用额度'})
    settlement_cycle = Integer(metadata={'description': '结算周期（天）'})
    cross_border_platform_ids = Dict(metadata={'description': '跨境平台账号'})
    
    # 附件与备注
    attachments = List(Dict(), metadata={'description': '附件列表'})
    notes = String(metadata={'description': '备注'})

class CompanyUpdateSchema(Schema):
    """更新公司Schema"""
    # 基础信息
    legal_name = String(metadata={'description': '法定名称'})
    short_name = String(metadata={'description': '简称'})
    english_name = String(metadata={'description': '英文名称'})
    company_type = String(metadata={'description': '公司类型'})
    status = String(metadata={'description': '状态'})
    
    # 证照信息
    unified_social_credit_code = String(metadata={'description': '统一社会信用代码 (五证合一)'})
    tax_id = String(metadata={'description': '纳税人识别号 (已废弃，请使用统一社会信用代码)', 'deprecated': True})
    business_license_no = String(metadata={'description': '营业执照注册号 (已废弃，请使用统一社会信用代码)', 'deprecated': True})
    business_license_issue_date = Date(metadata={'description': '营业执照发证日期'})
    business_license_expiry_date = Date(metadata={'description': '营业执照有效期'})
    business_scope = String(metadata={'description': '经营范围'})
    
    # 地址信息
    registered_address = String(metadata={'description': '注册地址'})
    business_address = String(metadata={'description': '经营地址'})
    postal_code = String(metadata={'description': '邮政编码'})
    
    # 联系信息
    contact_person = String(metadata={'description': '联系人'})
    contact_phone = String(metadata={'description': '联系电话'})
    contact_email = String(metadata={'description': '联系邮箱'})
    fax = String(metadata={'description': '传真'})
    
    # 财务信息
    bank_accounts = List(Dict(), metadata={'description': '银行账户列表'})
    tax_rate = Float(metadata={'description': '增值税率'})
    tax_registration_date = Date(metadata={'description': '税务登记日期'})
    
    # 跨境业务
    customs_code = String(metadata={'description': '海关编码 (CR Code)'})
    customs_registration_no = String(metadata={'description': '海关注册登记编号 (已废弃)', 'deprecated': True})
    inspection_code = String(metadata={'description': '检验检疫代码 (已废弃)', 'deprecated': True})
    foreign_trade_operator_code = String(metadata={'description': '对外贸易经营者备案号'})
    forex_account = String(metadata={'description': '外汇账户 (已移动至银行账户)', 'deprecated': True})
    forex_registration_no = String(metadata={'description': '外汇登记证号 (已废弃)', 'deprecated': True})
    
    # 资质证照
    import_export_license_no = String(metadata={'description': '进出口许可证号 (已废弃，一般贸易无需)', 'deprecated': True})
    import_export_license_expiry = Date(metadata={'description': '进出口许可证有效期 (已废弃)', 'deprecated': True})
    special_licenses = List(Dict(), metadata={'description': '特殊资质列表'})
    
    # 业务配置
    default_currency = String(metadata={'description': '默认币种'})
    default_payment_term = String(metadata={'description': '默认付款条款'})
    credit_limit = Decimal(places=2, metadata={'description': '信用额度'})
    settlement_cycle = Integer(metadata={'description': '结算周期（天）'})
    cross_border_platform_ids = Dict(metadata={'description': '跨境平台账号'})
    
    # 附件与备注
    attachments = List(Dict(), metadata={'description': '附件列表'})
    notes = String(metadata={'description': '备注'})
    updated_by = Integer(metadata={'description': '更新人ID'})

class HSCodeSimpleSchema(Schema):
    id = Integer()
    code = String()
    name = String()
    unit_1 = String()
    unit_2 = String()
    default_transaction_unit = String()
    refund_rate = Float()
    import_mfn_rate = Float()
    import_general_rate = Float()
    vat_rate = Float()
    regulatory_code = String()
    inspection_code = String()
    elements = String()
    note = String()
    updated_at = Date()

class HSCodeCreateSchema(Schema):
    code = String(required=True)
    name = String(required=True)
    unit_1 = String()
    unit_2 = String()
    default_transaction_unit = String()
    refund_rate = Float(required=True)
    import_mfn_rate = Float()
    import_general_rate = Float()
    vat_rate = Float()
    regulatory_code = String()
    inspection_code = String()
    elements = String()
    note = String()

class HSCodeUpdateSchema(Schema):
    code = String()
    name = String()
    unit_1 = String()
    unit_2 = String()
    default_transaction_unit = String()
    refund_rate = Float()
    import_mfn_rate = Float()
    import_general_rate = Float()
    vat_rate = Float()
    regulatory_code = String()
    inspection_code = String()
    elements = String()
    note = String()

class TaxCategorySchema(Schema):
    id = Integer()
    code = String()
    name = String()
    short_name = String()
    description = String()
    reference_rate = Decimal(places=4)
