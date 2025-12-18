import click
from flask.cli import AppGroup
from app.extensions import db
from sqlalchemy import select, update

# 定义一个 group 容器，用于后续可能的扩展，但在 __init__.py 中我们会单独导出 command
system_cli = AppGroup('system')

@click.command('seed-system-dicts')
@click.option('--clear', is_flag=True, help='清除现有数据')
def seed_system_dicts_cmd(clear):
    """生成系统字典数据"""
    from app.models.system import SysDict
    
    dictionaries = [
        # --- 1. 采购与供应商模块 (SRM) ---
        {
            "name": "供应商类型",
            "code": "supplier_type",
            "category": "purchase",
            "description": "用于供应商建档时的类型分类",
            "is_system": True,
            "value_options": [
                {"label": "生产商", "value": "manufacturer"},
                {"label": "贸易商", "value": "trader"},
                {"label": "服务商", "value": "service_provider"}
            ]
        },
        {
            "name": "供应商状态",
            "code": "supplier_status",
            "category": "purchase",
            "description": "控制供应商的业务状态",
            "is_system": True,
            "value_options": [
                {"label": "活跃", "value": "active"},
                {"label": "停用", "value": "inactive"},
                {"label": "潜在", "value": "potential"},
                {"label": "黑名单", "value": "blacklisted"}
            ]
        },
        {
            "name": "供应商等级",
            "code": "supplier_grade",
            "category": "purchase",
            "description": "供应商绩效评估等级",
            "is_system": True,
            "value_options": [
                {"label": "战略级", "value": "A"},
                {"label": "优质", "value": "B"},
                {"label": "合格", "value": "C"},
                {"label": "淘汰", "value": "D"}
            ]
        },
        {
            "name": "纳税人类型",
            "code": "taxpayer_type",
            "category": "purchase",
            "description": "影响开票税率和财务计算",
            "is_system": True,
            "value_options": [
                {"label": "一般纳税人", "value": "general"},
                {"label": "小规模纳税人", "value": "small"}
            ]
        },
        # --- 2. 财务与支付模块 (Finance) ---
        {
            "name": "币种",
            "code": "currency",
            "category": "finance",
            "description": "全局通用的货币选择",
            "is_system": True,
            "value_options": [
                {"label": "人民币", "value": "CNY"},
                {"label": "美元", "value": "USD"},
                {"label": "欧元", "value": "EUR"},
                {"label": "港币", "value": "HKD"}
            ]
        },
        {
            "name": "付款方式",
            "code": "payment_method",
            "category": "finance",
            "description": "采购合同和付款申请中使用",
            "is_system": True,
            "value_options": [
                {"label": "电汇", "value": "T/T"},
                {"label": "信用证", "value": "L/C"},
                {"label": "现金", "value": "Cash"},
                {"label": "支票", "value": "Check"},
                {"label": "汇票", "value": "Draft"}
            ]
        },
        {
            "name": "款项类型",
            "code": "payment_type",
            "category": "finance",
            "description": "明确付款的具体用途",
            "is_system": True,
            "value_options": [
                {"label": "定金", "value": "deposit"},
                {"label": "尾款", "value": "balance"},
                {"label": "预付", "value": "prepay"},
                {"label": "税金", "value": "tax"}
            ]
        },
        {
            "name": "结算状态",
            "code": "settlement_status",
            "category": "finance",
            "description": "付款单据的支付进度",
            "is_system": True,
            "value_options": [
                {"label": "未付", "value": "unpaid"},
                {"label": "部分支付", "value": "partial"},
                {"label": "已结清", "value": "paid"}
            ]
        },
        # --- 3. 产品与供应链模块 (SCM) ---
        {
            "name": "产品质量类型",
            "code": "product_quality_type",
            "category": "product",
            "description": "定义 SKU 的品质属性",
            "is_system": True,
            "value_options": [
                {"label": "售后件", "value": "Aftermarket"},
                {"label": "原厂件", "value": "OEM"},
                {"label": "翻新件", "value": "Refurbished"}
            ]
        },
        {
            "name": "参考码类型",
            "code": "product_code_type",
            "category": "product",
            "description": "产品关联号码的分类",
            "is_system": True,
            "value_options": [
                {"label": "原厂编码", "value": "OE"},
                {"label": "代工厂编码", "value": "OEM"},
                {"label": "北美通用码", "value": "PARTSLINK"}
            ]
        },
        {
            "name": "合同状态",
            "code": "contract_status",
            "category": "supply",
            "description": "交付合同的生命周期状态",
            "is_system": True,
            "value_options": [
                {"label": "待结算", "value": "pending"},
                {"label": "结算中", "value": "settling"},
                {"label": "已结算", "value": "settled"}
            ]
        },
        {
            "name": "单据来源",
            "code": "source_doc_type",
            "category": "supply",
            "description": "追溯业务数据的来源",
            "is_system": True,
            "value_options": [
                {"label": "出口装箱单", "value": "PL_EXPORT"},
                {"label": "入库单", "value": "GRN_STOCK"},
                {"label": "手工录入", "value": "MANUAL"}
            ]
        },
        {
            "name": "SKU变体后缀",
            "code": "sku_suffix",
            "category": "product",
            "description": "标准化的SKU后缀代码",
            "is_system": True,
            "value_options": [
                {"label": "左侧 (L)", "value": "-L"},
                {"label": "右侧 (R)", "value": "-R"},
                {"label": "套装 (SET)", "value": "-SET"},
                {"label": "售后件 (AM)", "value": "-AM"},
                {"label": "原厂件 (OEM)", "value": "-OEM"},
                {"label": "通用 (GEN)", "value": "-GEN"}
            ]
        },
        # --- 4. 产品元数据配置 ---
        {
            "name": "车型层级定义",
            "code": "vehicle_level_type",
            "category": "product",
            "description": "定义汽车层级结构的逻辑关系与约束",
            "is_system": True,
            "value_options": [
                {
                    "label": "制造商 (Make)", 
                    "value": "make", 
                    "meta": {"order": 10, "parent": None, "required": True}
                },
                {
                    "label": "车系 (Series)", 
                    "value": "series", 
                    "meta": {"order": 15, "parent": "make", "required": False} 
                },
                {
                    "label": "车型 (Model)", 
                    "value": "model", 
                    "meta": {"order": 20, "parent": "make", "required": True}
                },
                {
                    "label": "年份 (Year)", 
                    "value": "year", 
                    "meta": {"order": 30, "parent": "model", "required": True}
                },
                {
                    "label": "引擎 (Engine)", 
                    "value": "engine", 
                    "meta": {"order": 40, "parent": "year", "required": False}
                },
                {
                    "label": "配置 (Trim)", 
                    "value": "trim", 
                    "meta": {"order": 50, "parent": "year", "required": False}
                }
            ]
        },
        {
            "name": "商品属性分组",
            "code": "product_attribute_group",
            "category": "product",
            "description": "用于商品属性定义的逻辑分组，如：基本信息、技术参数等",
            "is_system": True,
            "value_options": [
                {
                    "label": "基本信息",
                    "value": "Basic",
                    "sort_order": 1
                },
                {
                    "label": "技术参数",
                    "value": "Technical",
                    "sort_order": 2
                },
                {
                    "label": "包装规格",
                    "value": "Packaging",
                    "sort_order": 3
                },
                {
                    "label": "物流信息",
                    "value": "Logistics",
                    "sort_order": 4
                }
            ]
        },
        # --- 5. 关务模块 (Customs) ---
        {
            "name": "国家/地区",
            "code": "country",
            "category": "customs",
            "description": "世界各国和地区代码",
            "is_system": True,
            "value_options": [
                {"label": "中国 (CHN)", "value": "中国"},
                {"label": "美国 (USA)", "value": "美国"},
                {"label": "英国 (GBR)", "value": "英国"},
                {"label": "德国 (DEU)", "value": "德国"},
                {"label": "日本 (JPN)", "value": "日本"},
                {"label": "韩国 (KOR)", "value": "韩国"},
                {"label": "法国 (FRA)", "value": "法国"},
                {"label": "加拿大 (CAN)", "value": "加拿大"},
                {"label": "澳大利亚 (AUS)", "value": "澳大利亚"},
                {"label": "意大利 (ITA)", "value": "意大利"},
                {"label": "西班牙 (ESP)", "value": "西班牙"},
                {"label": "荷兰 (NLD)", "value": "荷兰"},
                {"label": "俄罗斯 (RUS)", "value": "俄罗斯"},
                {"label": "越南 (VNM)", "value": "越南"},
                {"label": "印度 (IND)", "value": "印度"},
                {"label": "墨西哥 (MEX)", "value": "墨西哥"},
                {"label": "巴西 (BRA)", "value": "巴西"}
            ]
        },
        {
            "name": "港口/口岸",
            "code": "port",
            "category": "customs",
            "description": "常用进出口港口和口岸",
            "is_system": True,
            "value_options": [
                {"label": "宁波港", "value": "宁波港"},
                {"label": "上海港", "value": "上海港"},
                {"label": "深圳港", "value": "深圳港"},
                {"label": "洋山海关", "value": "洋山海关"},
                {"label": "北仑海关", "value": "北仑海关"},
                {"label": "梅山海关", "value": "梅山海关"},
                {"label": "大榭海关", "value": "大榭海关"},
                {"label": "浦东机场", "value": "浦东机场"},
                {"label": "白云机场", "value": "白云机场"},
                {"label": "深圳湾口岸", "value": "深圳湾口岸"},
                {"label": "青岛港", "value": "青岛港"},
                {"label": "天津港", "value": "天津港"},
                {"label": "厦门港", "value": "厦门港"}
            ]
        },
        {
            "name": "成交方式",
            "code": "transaction_mode",
            "category": "customs",
            "description": "国际贸易术语解释通则 (Incoterms)",
            "is_system": True,
            "value_options": [
                {"label": "CIF", "value": "CIF"},
                {"label": "FOB", "value": "FOB"},
                {"label": "EXW", "value": "EXW"},
                {"label": "FCA", "value": "FCA"},
                {"label": "CIP", "value": "CIP"},
                {"label": "DDP", "value": "DDP"},
                {"label": "DDU", "value": "DDU"},
                {"label": "DAP", "value": "DAP"},
                {"label": "C&F", "value": "C&F"}
            ]
        },
        {
            "name": "监管方式",
            "code": "trade_mode",
            "category": "customs",
            "description": "海关监管方式代码",
            "is_system": True,
            "value_options": [
                {"label": "0110 一般贸易", "value": "0110"},
                {"label": "9610 跨境电商", "value": "9610"},
                {"label": "9710 B2B直接出口", "value": "9710"},
                {"label": "9810 出口海外仓", "value": "9810"},
                {"label": "1039 市场采购", "value": "1039"}
            ]
        },
        {
            "name": "征免性质",
            "code": "nature_of_exemption",
            "category": "customs",
            "description": "海关征免性质分类",
            "is_system": True,
            "value_options": [
                {"label": "101 一般征税", "value": "101"},
                {"label": "502 进料加工", "value": "502"},
                {"label": "503 进料深加工", "value": "503"}
            ]
        },
        {
            "name": "运输方式",
            "code": "transport_mode",
            "category": "customs",
            "description": "进出口货物运输方式",
            "is_system": True,
            "value_options": [
                {"label": "2 水路运输", "value": "2"},
                {"label": "5 航空运输", "value": "5"},
                {"label": "4 公路运输", "value": "4"},
                {"label": "9 铁路运输", "value": "9"}
            ]
        },
        {
            "name": "海关申报单位",
            "code": "customs_unit",
            "category": "customs",
            "description": "海关法定的标准计量单位代码",
            "is_system": True,
            "value_options": [
                {"label": "007 个", "value": "007"},
                {"label": "035 千克", "value": "035"},
                {"label": "001 台", "value": "001"},
                {"label": "006 套", "value": "006"},
                {"label": "011 双", "value": "011"},
                {"label": "012 支", "value": "012"},
                {"label": "015 包", "value": "015"},
                {"label": "008 只", "value": "008"},
                {"label": "120 箱", "value": "120"},
                {"label": "010 件", "value": "010"},
                {"label": "005 辆", "value": "005"}
            ]
        }
    ]

    if clear:
        click.echo("正在清除现有字典数据...")
        db.session.query(SysDict).delete()
        db.session.commit()
        click.echo("✅ 已清除字典数据")

    click.echo("开始生成系统字典数据...")
    for data in dictionaries:
        existing = db.session.scalar(select(SysDict).where(SysDict.code == data['code']))
        if existing:
            click.echo(f"Updating existing dictionary: {data['name']} ({data['code']})")
            stmt = (
                update(SysDict)
                .where(SysDict.code == data['code'])
                .values(
                    name=data['name'],
                    category=data['category'],
                    description=data['description'],
                    is_system=data['is_system'],
                    value_options=data['value_options']
                )
            )
            db.session.execute(stmt)
        else:
            click.echo(f"Creating new dictionary: {data['name']} ({data['code']})")
            d = SysDict(**data)
            db.session.add(d)
    
    db.session.commit()
    click.echo("✅ 系统字典数据生成完成！")
    
    from app.models.serc.finance import SysPaymentTerm
    
    terms_data = [
        {'code': 'PIA', 'name': '预付 100% (PIA)', 'baseline': 'event_date', 'days_offset': 0},
        {'code': 'COD', 'name': '货到付款 (COD)', 'baseline': 'delivery_date', 'days_offset': 0},
        {'code': 'NET30', 'name': '月结 30 天 (NET30)', 'baseline': 'event_date', 'days_offset': 30},
        {'code': 'NET60', 'name': '月结 60 天 (NET60)', 'baseline': 'event_date', 'days_offset': 60},
        {'code': 'NET90', 'name': '月结 90 天 (NET90)', 'baseline': 'event_date', 'days_offset': 90},
        {'code': 'EOM15', 'name': '次月 15 号结 (EOM15)', 'baseline': 'event_date', 'days_offset': 15}, # 简化处理，实际需要特殊逻辑
    ]
    
    if clear:
            db.session.query(SysPaymentTerm).delete()
            db.session.commit()
            click.echo("✅ 已清除付款条款数据")
            
    for data in terms_data:
        exists = db.session.query(SysPaymentTerm).filter_by(code=data['code']).first()
        if not exists:
            term = SysPaymentTerm(**data)
            db.session.add(term)
    
    db.session.commit()
    click.echo("✅ 付款条款配置数据生成完成！")

@click.command('seed-companies')
@click.option('--clear', is_flag=True, help='清除现有数据')
def seed_companies_cmd(clear):
    """生成内部采购主体（公司）数据"""
    from app.models.serc.foundation import SysCompany
    
    # 预定义公司数据
    companies_data = [
        {
            'legal_name': '深圳未来科技有限公司',
            'short_name': '深圳未来',
            'code': 'SZ',
            'english_name': 'Shenzhen Future Tech Co., Ltd.',
            'unified_social_credit_code': '91440300MA5G123456',
            'registered_address': '深圳市南山区粤海街道科技园',
            'business_address': '深圳市南山区粤海街道科技园',
            'contact_person': '张经理',
            'contact_phone': '0755-88888888',
            'company_type': 'limited',
            'default_currency': 'CNY'
        },
        {
            'legal_name': '北京创新商贸有限公司',
            'short_name': '北京创新',
            'code': 'BJ',
            'english_name': 'Beijing Innovation Trading Co., Ltd.',
            'unified_social_credit_code': '91110108MA01234567',
            'registered_address': '北京市海淀区中关村大街',
            'business_address': '北京市海淀区中关村大街',
            'contact_person': '李总监',
            'contact_phone': '010-66666666',
            'company_type': 'limited',
            'default_currency': 'CNY'
        },
        {
            'legal_name': '香港全球供应链有限公司',
            'short_name': '香港全球',
            'code': 'HK',
            'english_name': 'HK Global Supply Chain Ltd.',
            'unified_social_credit_code': 'HK12345678',
            'registered_address': '香港九龙尖沙咀',
            'business_address': '香港九龙尖沙咀',
            'contact_person': 'Michael Wong',
            'contact_phone': '+852 2345 6789',
            'company_type': 'limited',
            'default_currency': 'USD'
        }
    ]

    if clear:
        click.echo("正在清除现有内部公司数据...")
        db.session.query(SysCompany).delete()
        db.session.commit()
        click.echo("✅ 已清除内部公司数据")

    for c_data in companies_data:
        company = SysCompany(**c_data)
        # 检查是否已存在 (根据 code)
        exists = db.session.query(SysCompany).filter_by(code=c_data['code']).first()
        if not exists:
            db.session.add(company)
            click.echo(f"添加公司: {c_data['legal_name']} ({c_data['code']})")
        else:
            click.echo(f"公司已存在: {c_data['legal_name']} ({c_data['code']})")
    
    db.session.commit()
    click.echo("✅ 内部公司数据生成完成！")

@click.command('seed-hscodes')
@click.option('--clear', is_flag=True, help='清除现有数据')
def seed_hscodes_cmd(clear):
    """生成 HS Code 模拟数据 (中国海关标准)"""
    from app.models.serc.foundation import SysHSCode
    
    # 模拟数据源
    hscodes_data = [
        {
            "code": "8512201000",
            "name": "机动车辆用照明装置",
            "unit_1": "千克",
            "unit_2": "个",
            "default_transaction_unit": "个",
            "refund_rate": 0.1300,
            "import_mfn_rate": 0.1000,
            "import_general_rate": 0.3500,
            "vat_rate": 0.1300,
            "regulatory_code": "A",
            "inspection_code": "M",
            "elements": "1:品名;2:适用车型;3:品牌;4:型号;5:电压;6:功率;7:材质",
            "note": "主要包含前大灯、尾灯等，需注意是否带光源"
        },
        {
            "code": "8708999990",
            "name": "其他未列名机动车辆零件、附件",
            "unit_1": "千克",
            "unit_2": None,
            "default_transaction_unit": "个",
            "refund_rate": 0.1300,
            "import_mfn_rate": 0.0600,
            "import_general_rate": 0.4500,
            "vat_rate": 0.1300,
            "regulatory_code": None,
            "inspection_code": None,
            "elements": "1:品名;2:品牌;3:适用车型;4:型号;5:零部件编号",
            "note": "通用兜底编码，适用于无明确归类的汽配零件"
        },
        {
            "code": "3926909090",
            "name": "其他塑料制品",
            "unit_1": "千克",
            "unit_2": None,
            "default_transaction_unit": "个",
            "refund_rate": 0.1300,
            "import_mfn_rate": 0.0650,
            "import_general_rate": 0.8000,
            "vat_rate": 0.1300,
            "regulatory_code": None,
            "inspection_code": None,
            "elements": "1:品名;2:用途;3:材质;4:品牌;5:型号",
            "note": "适用于塑料材质的内饰件、卡扣等"
        },
        {
            "code": "8708299000",
            "name": "其他车身未列名零部件",
            "unit_1": "千克",
            "unit_2": None,
            "default_transaction_unit": "个",
            "refund_rate": 0.1300,
            "import_mfn_rate": 0.0600,
            "import_general_rate": 0.4500,
            "vat_rate": 0.1300,
            "regulatory_code": "AB",
            "inspection_code": "M/N",
            "elements": "1:品名;2:适用车型;3:品牌;4:型号;5:材质",
            "note": "适用于叶子板、保险杠支架等车身结构件"
        },
        {
            "code": "8544302000",
            "name": "机动车辆用点火布线组及其他布线组",
            "unit_1": "千克",
            "unit_2": "组",
            "default_transaction_unit": "套",
            "refund_rate": 0.1300,
            "import_mfn_rate": 0.1000,
            "import_general_rate": 0.3500,
            "vat_rate": 0.1300,
            "regulatory_code": None,
            "inspection_code": None,
            "elements": "1:品名;2:用途;3:电压;4:品牌;5:型号",
            "note": "线束类产品"
        }
    ]

    if clear:
        click.echo("正在清除现有 HS Code 数据...")
        db.session.query(SysHSCode).delete()
        db.session.commit()
        click.echo("✅ 已清除 HS Code 数据")

    for data in hscodes_data:
        existing = db.session.scalar(select(SysHSCode).where(SysHSCode.code == data['code']))
        if existing:
            click.echo(f"Updating HS Code: {data['code']}")
            stmt = (
                update(SysHSCode)
                .where(SysHSCode.code == data['code'])
                .values(**data)
            )
            db.session.execute(stmt)
        else:
            click.echo(f"Creating HS Code: {data['code']}")
            hs = SysHSCode(**data)
            db.session.add(hs)
    
    db.session.commit()
    click.echo("✅ HS Code 模拟数据生成完成！")

# 注册到 Group
system_cli.add_command(seed_system_dicts_cmd)
system_cli.add_command(seed_companies_cmd)
system_cli.add_command(seed_hscodes_cmd)

