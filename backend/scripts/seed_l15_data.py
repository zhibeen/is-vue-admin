import logging
from decimal import Decimal
from app.extensions import db
from app.models.product import SysTaxCategory, Product, SkuSuffix
from app.models.purchase.supplier import SysSupplier

logger = logging.getLogger(__name__)

def seed_l15_data():
    """初始化L1.5税务相关数据及产品辅助数据"""
    logger.info("开始初始化 L1.5 税务及辅助数据...")

    # 0. Seed SkuSuffix
    suffixes = [
        {'code': 'L', 'meaning_en': 'Left', 'meaning_cn': '左侧'},
        {'code': 'R', 'meaning_en': 'Right', 'meaning_cn': '右侧'},
        {'code': 'SET', 'meaning_en': 'Set', 'meaning_cn': '套装'},
        {'code': 'PAIR', 'meaning_en': 'Pair', 'meaning_cn': '对装'},
    ]
    
    for item in suffixes:
        suf = db.session.get(SkuSuffix, item['code'])
        if not suf:
            suf = SkuSuffix(**item)
            db.session.add(suf)
            logger.info(f"创建SKU后缀: {item['code']}")
    
    db.session.flush()

    # 1. Seed SysTaxCategory
    tax_categories = [
        {
            'code': '109010101', 
            'name': '汽车配件-车灯', 
            'short_name': '车灯',
            'reference_rate': Decimal('0.13')
        },
        {
            'code': '109010202', 
            'name': '塑料制品-支架', 
            'short_name': '塑料制品',
            'reference_rate': Decimal('0.13')
        },
        {
            'code': '109050505', 
            'name': '五金制品-控制臂', 
            'short_name': '五金件',
            'reference_rate': Decimal('0.13')
        }
    ]

    tax_cat_map = {}
    for item in tax_categories:
        cat = db.session.query(SysTaxCategory).filter_by(code=item['code']).first()
        if not cat:
            cat = SysTaxCategory(**item)
            db.session.add(cat)
            logger.info(f"创建税收分类: {item['code']}")
        else:
            cat.name = item['name']
            cat.short_name = item['short_name']
            cat.reference_rate = item['reference_rate']
        db.session.flush()
        tax_cat_map[item['code']] = cat

    # 2. Update Suppliers with Taxpayer Info
    # Ensure we have some suppliers first (assuming seed_suppliers ran or db has data)
    # If not, create dummy ones
    
    suppliers_data = [
        {
            'code': 'SUP-001', # General Taxpayer
            'name': 'Guangzhou Auto Parts Co., Ltd.',
            'taxpayer_type': 'general',
            'default_vat_rate': Decimal('0.13')
        },
        {
            'code': 'SUP-002', # Small Taxpayer
            'name': 'Yiwu Small Commodity Factory',
            'taxpayer_type': 'small',
            'default_vat_rate': Decimal('0.03')
        }
    ]

    for s_data in suppliers_data:
        supplier = db.session.query(SysSupplier).filter_by(code=s_data['code']).first()
        if supplier:
            supplier.taxpayer_type = s_data['taxpayer_type']
            supplier.default_vat_rate = s_data['default_vat_rate']
            logger.info(f"更新供应商税率信息: {supplier.name} -> {supplier.default_vat_rate}")
        else:
            # Create if not exists (minimal fields)
            supplier = SysSupplier(
                code=s_data['code'],
                name=s_data['name'],
                taxpayer_type=s_data['taxpayer_type'],
                default_vat_rate=s_data['default_vat_rate']
            )
            db.session.add(supplier)
            logger.info(f"创建供应商: {supplier.name}")
    
    # 3. Link Products to Tax Categories
    # Mapping SKU to Tax Code
    # Assuming products from seed_products.py exist: SKU-001, SKU-002, SKU-003
    sku_tax_map = {
        'SKU-001': '109010101', # LED Headlight -> 车灯
        'SKU-002': '109010202', # Plastic Bracket -> 塑料制品
        'SKU-003': '109050505', # Control Arm -> 五金件
    }

    for sku, tax_code in sku_tax_map.items():
        product = db.session.query(Product).filter_by(sku=sku).first()
        if product and tax_code in tax_cat_map:
            product.tax_category_id = tax_cat_map[tax_code].id
            logger.info(f"关联产品税收分类: {sku} -> {tax_code}")

    db.session.commit()
    logger.info("L1.5 税务数据初始化完成")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_l15_data()

