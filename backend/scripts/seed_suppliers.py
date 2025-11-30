"""
生成虚拟供应商数据的脚本
"""
import random
from faker import Faker
from app import create_app
from app.extensions import db
from app.models.purchase.supplier import SysSupplier

# 创建 Faker 实例（中文和英文混合）
fake_zh = Faker('zh_CN')
fake_en = Faker('en_US')

# 供应商类型
SUPPLIER_TYPES = ['manufacturer', 'trader', 'service_provider', 'other']
# 状态
STATUSES = ['active', 'inactive', 'potential', 'blacklisted']
# 等级
GRADES = ['A', 'B', 'C', 'D', None]
# 币种
CURRENCIES = ['CNY', 'USD', 'EUR', 'JPY', 'HKD']
# 国家
COUNTRIES = ['中国', '美国', '日本', '德国', '韩国', '新加坡', '英国', '法国']

# 公司名称后缀
COMPANY_SUFFIXES_ZH = [
    '科技有限公司', '电子有限公司', '贸易有限公司', '实业有限公司',
    '国际贸易有限公司', '进出口有限公司', '制造有限公司', '工业有限公司',
    '集团有限公司', '股份有限公司'
]

COMPANY_SUFFIXES_EN = [
    'Ltd.', 'Inc.', 'Corp.', 'Co., Ltd.', 'International',
    'Electronics', 'Technology', 'Industries', 'Manufacturing', 'Trading'
]

# 公司名称前缀
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

def generate_supplier_code(index):
    """生成供应商代码"""
    return f"SUP-{index:04d}"

def generate_company_name(is_chinese=True):
    """生成公司名称"""
    if is_chinese:
        prefix = random.choice(COMPANY_PREFIXES_ZH)
        suffix = random.choice(COMPANY_SUFFIXES_ZH)
        return f"{prefix}{suffix}"
    else:
        prefix = random.choice(COMPANY_PREFIXES_EN)
        suffix = random.choice(COMPANY_SUFFIXES_EN)
        return f"{prefix} {suffix}"

def generate_short_name(name, is_chinese=True):
    """生成简称"""
    if is_chinese:
        # 取前2-4个字符
        length = min(random.randint(2, 4), len(name))
        return name[:length]
    else:
        # 取首字母缩写
        words = name.split()
        return ''.join([w[0] for w in words[:3]]).upper()

def generate_contacts():
    """生成联系人列表"""
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
    """生成银行账户列表"""
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

def clear_suppliers():
    """清除所有供应商数据"""
    print("正在清除现有供应商数据...")
    count = db.session.query(SysSupplier).delete()
    db.session.commit()
    print(f"已清除 {count} 条供应商数据")

def seed_suppliers(count=50):
    """生成虚拟供应商数据"""
    print(f"开始生成 {count} 条虚拟供应商数据...")
    
    suppliers = []
    for i in range(1, count + 1):
        is_chinese = random.choice([True, False])
        name = generate_company_name(is_chinese)
        short_name = generate_short_name(name, is_chinese)
        supplier_type = random.choice(SUPPLIER_TYPES)
        
        # 根据类型调整状态和等级的概率
        if supplier_type == 'manufacturer':
            status = random.choices(STATUSES, weights=[70, 10, 15, 5])[0]
            grade = random.choices(GRADES, weights=[30, 40, 20, 5, 5])[0]
        elif supplier_type == 'trader':
            status = random.choices(STATUSES, weights=[60, 15, 20, 5])[0]
            grade = random.choices(GRADES, weights=[20, 40, 30, 5, 5])[0]
        else:
            status = random.choices(STATUSES, weights=[50, 20, 25, 5])[0]
            grade = random.choices(GRADES, weights=[10, 30, 40, 10, 10])[0]
        
        supplier = SysSupplier(
            code=generate_supplier_code(i),
            name=name,
            short_name=short_name,
            supplier_type=supplier_type,
            status=status,
            grade=grade,
            
            # 联系信息
            country=random.choice(COUNTRIES),
            province=fake_zh.province() if is_chinese else None,
            city=fake_zh.city() if is_chinese else fake_en.city(),
            address=fake_zh.address() if is_chinese else fake_en.address(),
            website=fake_en.url(),
            
            primary_contact=fake_zh.name(),
            primary_phone=fake_zh.phone_number(),
            primary_email=fake_en.email(),
            contacts=generate_contacts(),
            
            # 财务信息
            tax_id=fake_zh.ssn() if is_chinese else fake_en.ssn(),
            currency=random.choice(CURRENCIES),
            payment_terms=random.choice(['30天', '60天', '90天', 'T/T', 'L/C', '预付30%']),
            payment_method=random.choice(['电汇', '信用证', '承兑汇票', '现金', '支票']),
            bank_accounts=generate_bank_accounts(),
            
            # 运营参数
            lead_time_days=random.randint(7, 90),
            moq=f"{random.randint(100, 10000)} 件",
            
            # 管理信息
            notes=fake_zh.text(max_nb_chars=100) if random.random() > 0.5 else None,
            tags=[random.choice(['优质', '长期合作', '新供应商', '重点关注', 'VIP'])] if random.random() > 0.3 else []
        )
        
        suppliers.append(supplier)
        
        # 每10条打印一次进度
        if i % 10 == 0:
            print(f"已生成 {i}/{count} 条数据...")
    
    # 批量插入
    db.session.bulk_save_objects(suppliers)
    db.session.commit()
    print(f"✅ 成功生成 {count} 条虚拟供应商数据！")

def main():
    """主函数"""
    app = create_app()
    with app.app_context():
        # 清除旧数据
        clear_suppliers()
        
        # 生成新数据
        seed_suppliers(50)

if __name__ == '__main__':
    main()
