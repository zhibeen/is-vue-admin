import click
import random
from faker import Faker
from flask.cli import AppGroup
from app.extensions import db

supply_cli = AppGroup('supply')

@click.command('seed-suppliers')
@click.option('--count', default=50, help='生成供应商数量')
@click.option('--clear', is_flag=True, help='清除现有数据')
def seed_suppliers_cmd(count, clear):
    """生成虚拟供应商数据"""
    from app.models.purchase.supplier import SysSupplier
    from app.models.serc.finance import SysPaymentTerm
    
    # 获取所有付款条款
    payment_terms = db.session.query(SysPaymentTerm).all()
    
    fake_zh = Faker('zh_CN')
    fake_en = Faker('en_US')
    
    # 供应商类型
    SUPPLIER_TYPES = ['manufacturer', 'trader', 'service_provider', 'other']
    STATUSES = ['active', 'inactive', 'potential', 'blacklisted']
    GRADES = ['A', 'B', 'C', 'D', None]
    CURRENCIES = ['CNY', 'USD', 'EUR', 'JPY', 'HKD']
    COUNTRIES = ['中国', '美国', '日本', '德国', '韩国', '新加坡', '英国', '法国']
    
    COMPANY_SUFFIXES_ZH = [
        '科技有限公司', '电子有限公司', '贸易有限公司', '实业有限公司',
        '国际贸易有限公司', '进出口有限公司', '制造有限公司', '工业有限公司',
        '集团有限公司', '股份有限公司'
    ]
    
    COMPANY_SUFFIXES_EN = [
        'Ltd.', 'Inc.', 'Corp.', 'Co., Ltd.', 'International',
        'Electronics', 'Technology', 'Industries', 'Manufacturing', 'Trading'
    ]
    
    COMPANY_PREFIXES_ZH = [
        '华为', '联想', '海尔', '美的', '格力', '小米', '比亚迪', '京东',
        '阿里', '腾讯', '百度', '中兴', 'TCL', '海信', '创维', '康佳',
        '长虹', '方正', '同方', '紫光', '浪潮', '曙光', '神州', '清华',
        '北大', '复旦', '交大', '中科', '国科', '航天', '航空', '中船',
        '中车', '中铁', '中建', '中电', '中石', '中海', '中粮', '中纺'
    ]
    
    COMPANY_PREFIXES_EN = [
        'Global', 'International', 'United', 'Advanced', 'Superior',
        'Premium', 'Elite', 'Prime', 'Mega', 'Ultra', 'Super', 'Tech',
        'Digital', 'Smart', 'Innovative', 'Pioneer', 'Leading', 'Top'
    ]
    
    def generate_company_name(is_chinese=True):
        if is_chinese:
            prefix = random.choice(COMPANY_PREFIXES_ZH)
            suffix = random.choice(COMPANY_SUFFIXES_ZH)
            return f"{prefix}{suffix}"
        else:
            prefix = random.choice(COMPANY_PREFIXES_EN)
            suffix = random.choice(COMPANY_SUFFIXES_EN)
            return f"{prefix} {suffix}"
    
    def generate_short_name(name, is_chinese=True):
        if is_chinese:
            length = min(random.randint(2, 4), len(name))
            return name[:length]
        else:
            words = name.split()
            return ''.join([w[0] for w in words[:3]]).upper()
    
    def generate_contacts():
        num_contacts = random.randint(1, 3)
        contacts = []
        for _ in range(num_contacts):
            contacts.append({
                'name': fake_zh.name(),
                'role': random.choice(['销售经理', '采购经理', '总经理', '业务员', '客服']),
                'phone': fake_zh.phone_number(),
                'email': fake_en.email()
            })
        return contacts
    
    def generate_bank_accounts():
        num_accounts = random.randint(1, 2)
        accounts = []
        banks = ['中国银行', '工商银行', '建设银行', '农业银行', '招商银行', '交通银行']
        for _ in range(num_accounts):
            accounts.append({
                'bank_name': random.choice(banks),
                'account': fake_zh.credit_card_number(),
                'currency': random.choice(['CNY', 'USD', 'EUR'])
            })
        return accounts
    
    # 清除旧数据
    if clear:
        click.echo("正在清除现有供应商数据...")
        deleted_count = db.session.query(SysSupplier).delete()
        db.session.commit()
        click.echo(f"✅ 已清除 {deleted_count} 条供应商数据")
    
    # 生成新数据
    click.echo(f"开始生成 {count} 条虚拟供应商数据...")
    
    # 获取当前最大的 supplier code 序号
    from sqlalchemy import func
    max_code = db.session.query(func.max(SysSupplier.code)).scalar()
    start_index = 1
    if max_code and max_code.startswith('SUP-'):
        try:
            start_index = int(max_code.split('-')[1]) + 1
        except ValueError:
            pass

    suppliers = []
    for i in range(start_index, start_index + count):
        is_chinese = random.choice([True, False])
        name = generate_company_name(is_chinese)
        short_name = generate_short_name(name, is_chinese)
        supplier_type = random.choice(SUPPLIER_TYPES)
        
        if supplier_type == 'manufacturer':
            status = random.choices(STATUSES, weights=[70, 10, 15, 5])[0]
            grade = random.choices(GRADES, weights=[30, 40, 20, 5, 5])[0]
        elif supplier_type == 'trader':
            status = random.choices(STATUSES, weights=[60, 15, 20, 5])[0]
            grade = random.choices(GRADES, weights=[20, 40, 30, 5, 5])[0]
        else:
            status = random.choices(STATUSES, weights=[50, 20, 25, 5])[0]
            grade = random.choices(GRADES, weights=[10, 30, 40, 10, 10])[0]
        
        # 随机分配一个付款条款
        payment_term = random.choice(payment_terms) if payment_terms else None
        
        supplier = SysSupplier(
            code=f"SUP-{i:04d}",
            name=name,
            short_name=short_name,
            supplier_type=supplier_type,
            status=status,
            grade=grade,
            country=random.choice(COUNTRIES),
            province=fake_zh.province() if is_chinese else None,
            city=fake_zh.city() if is_chinese else fake_en.city(),
            address=fake_zh.address() if is_chinese else fake_en.address(),
            website=fake_en.url(),
            primary_contact=fake_zh.name(),
            primary_phone=fake_zh.phone_number(),
            primary_email=fake_en.email(),
            contacts=generate_contacts(),
            tax_id=fake_zh.ssn() if is_chinese else fake_en.ssn(),
            currency=random.choice(CURRENCIES),
            # 使用结构化条款ID，同时保留文本快照
            payment_term_id=payment_term.id if payment_term else None,
            payment_terms=payment_term.name if payment_term else random.choice(['30天', '60天', '90天', 'T/T', 'L/C', '预付30%']),
            payment_method=random.choice(['电汇', '信用证', '承兑汇票', '现金', '支票']),
            bank_accounts=generate_bank_accounts(),
            lead_time_days=random.randint(7, 90),
            moq=f"{random.randint(100, 10000)} 件",
            notes=fake_zh.text(max_nb_chars=100) if random.random() > 0.5 else None,
            tags=[random.choice(['优质', '长期合作', '新供应商', '重点关注', 'VIP'])] if random.random() > 0.3 else []
        )
        
        suppliers.append(supplier)
        
        if (i - start_index + 1) % 10 == 0:
            click.echo(f"已生成 {i - start_index + 1}/{count} 条数据...")
    
    db.session.bulk_save_objects(suppliers)
    db.session.commit()
    click.echo(f"✅ 成功生成 {count} 条虚拟供应商数据！")

@click.command('seed-contracts')
@click.option('--count', default=20, help='生成合同数量')
@click.option('--clear', is_flag=True, help='清除现有数据')
def seed_contracts_cmd(count, clear):
    """生成虚拟交付合同数据"""
    from app.models.purchase.supplier import SysSupplier
    from app.models.product import Product
    from app.models.supply import ScmDeliveryContract, ScmDeliveryContractItem, ScmSourceDoc
    from app.services.serc.supply_service import supply_service
    from datetime import datetime, timedelta
    
    # 0. 清除旧数据 (可选)
    if clear:
        click.echo("正在清除现有交付合同数据 (包括明细和源单据)...")
        # 注意级联删除
        db.session.query(ScmDeliveryContractItem).delete()
        db.session.query(ScmDeliveryContract).delete()
        db.session.query(ScmSourceDoc).delete()
        db.session.commit()
        click.echo("✅ 已清除交付合同数据")

    # 1. 获取基础数据
    suppliers = db.session.query(SysSupplier).all()
    products = db.session.query(Product).all()
    # 获取内部公司 (采购主体)
    from app.models.serc.foundation import SysCompany
    companies = db.session.query(SysCompany).all()
    
    if not suppliers or not products:
        click.echo("错误: 数据库中缺少供应商或商品数据。")
        return
        
    if not companies:
        click.echo("提示: 数据库中缺少内部公司数据(SysCompany)，合同将不包含采购主体。建议先运行 flask seed-companies。")

    click.echo(f"开始生成 {count} 条交付合同数据...")

    # 2. 循环生成
    success_count = 0
    for i in range(count):
        supplier = random.choice(suppliers)
        company = random.choice(companies) if companies else None
        
        # 随机日期 (过去30天内)
        days_ago = random.randint(0, 30)
        event_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        delivery_date = (datetime.now() - timedelta(days=days_ago - 7)).strftime("%Y-%m-%d") # 交货期一般在业务日期之后
        
        # 随机商品明细 (1-5个商品)
        items = []
        num_items = random.randint(1, 5)
        selected_products = random.sample(products, min(num_items, len(products)))
        
        for prod in selected_products:
            qty = random.randint(10, 500)
            # 假设价格在 10-1000 之间 (元)
            price = random.randint(1000, 100000) / 100.0
            
            items.append({
                "product_id": prod.id,
                "confirmed_qty": qty,
                "unit_price": price,
                "notes": f"Auto generated item {i}-{prod.id}"
            })
        
        # 构造 payload
        payload = {
            "supplier_id": supplier.id,
            "company_id": company.id if company else None, # 传入采购主体
            "currency": "CNY",
            "event_date": event_date,
            "delivery_date": delivery_date,
            "delivery_address": company.registered_address if company else "公司仓库",
            "notes": f"系统自动生成的测试合同 - {i+1}",
            "items": items
        }
        
        try:
            # 每个循环使用独立的 transaction，避免 nested 错误
            # 注意：create_manual_contract 内部可能会 commit/flush
            
            contract = supply_service.create_manual_contract(payload)
            
            # 模拟部分已付款 (随机)
            from decimal import Decimal
            # 使用 Column 方案，直接更新 paid_amount 字段
            paid_ratio = random.choice([0, 0, 0.3, 0.5, 0.8, 1.0]) # 增加 0 的概率
            if paid_ratio > 0:
                paid_val = contract.total_amount * Decimal(str(paid_ratio))
                contract.paid_amount = paid_val
                
                # 如果全部付清，更新状态
                if paid_ratio == 1.0:
                    contract.status = 'settled'
                elif paid_ratio > 0:
                    contract.status = 'settling'
                
                db.session.add(contract)
                db.session.commit()
            
            success_count += 1
            if success_count % 5 == 0:
                click.echo(f"已生成 {success_count}/{count} 条合同...")
                
        except Exception as e:
            db.session.rollback()
            click.echo(f"[{i+1}] Error: {str(e)}")

    click.echo(f"✅ 完成！成功生成 {success_count} 条交付合同。")

supply_cli.add_command(seed_suppliers_cmd)
supply_cli.add_command(seed_contracts_cmd)

