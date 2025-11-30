import logging
from app.extensions import db
from app.models.product import Product
from app.models.serc.foundation import SysHSCode
from app.models.category import Category

logger = logging.getLogger(__name__)

def seed_products():
    """初始化商品及HS Code测试数据"""
    logger.info("开始初始化商品数据...")
    
    # 1. 初始化 HS Code
    hscodes = [
        {'code': '8708999990', 'name': '其他未列名机动车辆零件、附件', 'refund_rate': 0.13},
        {'code': '8512201000', 'name': '机动车辆用照明装置', 'refund_rate': 0.13},
        {'code': '3926909090', 'name': '其他塑料制品', 'refund_rate': 0.13},
    ]
    
    hs_map = {}
    for item in hscodes:
        hs = db.session.query(SysHSCode).filter_by(code=item['code']).first()
        if not hs:
            hs = SysHSCode(**item)
            db.session.add(hs)
            logger.info(f"创建 HS Code: {item['code']}")
        else:
            # 更新退税率
            hs.refund_rate = item['refund_rate']
            hs.name = item['name']
        db.session.flush()
        hs_map[item['code']] = hs

    # 2. 确保有分类
    category = db.session.query(Category).filter_by(name='Default').first()
    if not category:
        category = Category(name='Default', code='DEF')
        db.session.add(category)
        db.session.flush()

    # 3. 初始化商品
    products = [
        {
            'sku': 'SKU-001',
            'name': 'LED Headlight Assembly',
            'declared_name': 'LED大灯总成',
            'declared_unit': 'PCS',
            'hs_code': '8512201000',
            'price': 500.00
        },
        {
            'sku': 'SKU-002',
            'name': 'Plastic Bumper Bracket',
            'declared_name': '塑料保险杠支架',
            'declared_unit': 'PCS',
            'hs_code': '3926909090',
            'price': 45.50
        },
        {
            'sku': 'SKU-003',
            'name': 'Steel Control Arm',
            'declared_name': '钢制控制臂',
            'declared_unit': 'PCS',
            'hs_code': '8708999990',
            'price': 120.00
        }
    ]

    for p_data in products:
        product = db.session.query(Product).filter_by(sku=p_data['sku']).first()
        hs_obj = hs_map.get(p_data['hs_code'])
        
        if not product:
            product = Product(
                sku=p_data['sku'],
                name=p_data['name'],
                category_id=category.id,
                declared_name=p_data['declared_name'],
                declared_unit=p_data['declared_unit'],
                hs_code_id=hs_obj.id if hs_obj else None
            )
            db.session.add(product)
            logger.info(f"创建商品: {p_data['sku']}")
        else:
            # 更新关联
            product.hs_code_id = hs_obj.id if hs_obj else None
            product.declared_name = p_data['declared_name']
            
    db.session.commit()
    logger.info("商品数据初始化完成")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_products()

