import logging
from app.extensions import db
from app.models.product import Product, SkuSuffix
from app.models.serc.foundation import SysHSCode
from app.models.product import Category, AttributeDefinition, CategoryAttribute
from app.models.vehicle import VehicleAux

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
    categories = [
        {'name': '灯光系统', 'code': '101', 'children': [
            {'name': '前大灯', 'code': '01'},
            {'name': '尾灯', 'code': '02'}
        ]},
        {'name': '覆盖件', 'code': '201', 'children': [
            {'name': '保险杠', 'code': '01'},
            {'name': '叶子板', 'code': '02'}
        ]}
    ]
    
    category_map = {} # code -> Category Object

    for cat_data in categories:
        parent = db.session.query(Category).filter_by(code=cat_data['code']).first()
        if not parent:
            parent = Category(name=cat_data['name'], code=cat_data['code'])
            db.session.add(parent)
            db.session.flush()
        
        for child_data in cat_data.get('children', []):
            # child_data['code'] is suffix "01"
            # full_code = "10101"
            full_code = f"{parent.code}{child_data['code']}"
            
            child = db.session.query(Category).filter_by(code=full_code).first()
            if not child:
                child = Category(name=child_data['name'], code=full_code, parent_id=parent.id, is_leaf=True)
                db.session.add(child)
                db.session.flush()
            
            # Map using name (unique within this seed logic ideally, or store both)
            category_map[child_data['name']] = child

    # 3. 初始化 SkuSuffix
    # NOTE: Updated to match model fields (meaning_en, meaning_cn)
    suffixes = [
        {'code': 'L', 'meaning_en': 'Left', 'meaning_cn': '左侧'},
        {'code': 'R', 'meaning_en': 'Right', 'meaning_cn': '右侧'},
        {'code': 'SET', 'meaning_en': 'Set', 'meaning_cn': '套装'},
    ]
    for suf in suffixes:
        s = db.session.query(SkuSuffix).filter_by(code=suf['code']).first()
        if not s:
            s = SkuSuffix(**suf)
            db.session.add(s)
            logger.info(f"创建 SkuSuffix: {suf['code']}")
        else:
             s.meaning_en = suf['meaning_en']
             s.meaning_cn = suf['meaning_cn']

    # 4. 初始化 VehicleAux (Brands/Models)
    brands = [
        {'name': 'Toyota', 'code': 'TO', 'abbr': 'TY', 'models': ['Corolla', 'Camry']},
        {'name': 'Honda', 'code': 'HO', 'abbr': 'HD', 'models': ['Civic', 'Accord']},
    ]
    
    for b_data in brands:
        brand = db.session.query(VehicleAux).filter_by(code=b_data['code'], level_type='brand').first()
        if not brand:
            brand = VehicleAux(name=b_data['name'], code=b_data['code'], abbr=b_data['abbr'], level_type='brand')
            db.session.add(brand)
            db.session.flush()
            logger.info(f"创建品牌: {b_data['name']}")
        
        for m_name in b_data['models']:
            model = db.session.query(VehicleAux).filter_by(name=m_name, parent_id=brand.id, level_type='model').first()
            if not model:
                model = VehicleAux(name=m_name, parent_id=brand.id, level_type='model')
                db.session.add(model)
                logger.info(f"  创建车型: {m_name}")

    # 5. 初始化 Attribute Definitions & Link to Categories
    # 属性定义
    attrs_data = [
        {'key_name': 'voltage', 'label': '电压', 'data_type': 'select', 'options': [{'label': '12V', 'value': '12V'}, {'label': '24V', 'value': '24V'}]},
        {'key_name': 'bulb_type', 'label': '灯泡类型', 'data_type': 'text', 'options': []},
        {'key_name': 'material', 'label': '材质', 'data_type': 'text', 'options': []},
        {'key_name': 'color', 'label': '颜色', 'data_type': 'text', 'options': []},
        
        # 新增更多测试属性
        {'key_name': 'lens_color', 'label': '透镜颜色', 'data_type': 'select', 'options': ['Clear', 'Smoke', 'Amber']}, # 兼容字符串数组
        {'key_name': 'housing_color', 'label': '底壳颜色', 'data_type': 'text', 'options': []},
        {'key_name': 'bulbs_included', 'label': '含灯泡', 'data_type': 'boolean', 'options': []},
        
        # 更多通用汽配属性 (Attribute Definitions Only)
        # --- 基础物理属性 ---
        {'key_name': 'position', 'label': '安装位置', 'data_type': 'select', 'options': ['Front', 'Rear', 'Left', 'Right', 'Upper', 'Lower', 'Inner', 'Outer']},
        {'key_name': 'oe_number', 'label': 'OE号', 'data_type': 'text', 'options': []},
        {'key_name': 'part_number', 'label': '零件编号', 'data_type': 'text', 'options': []},
        {'key_name': 'universal_fitment', 'label': '通用性', 'data_type': 'boolean', 'options': []},
        {'key_name': 'material_composition', 'label': '材质成分', 'data_type': 'text', 'options': []},
        {'key_name': 'color_finish', 'label': '外观颜色', 'data_type': 'text', 'options': []},
        {'key_name': 'net_weight', 'label': '净重(kg)', 'data_type': 'number', 'options': []},
        {'key_name': 'gross_weight', 'label': '毛重(kg)', 'data_type': 'number', 'options': []},
        {'key_name': 'package_length', 'label': '包装长度(cm)', 'data_type': 'number', 'options': []},
        {'key_name': 'package_width', 'label': '包装宽度(cm)', 'data_type': 'number', 'options': []},
        {'key_name': 'package_height', 'label': '包装高度(cm)', 'data_type': 'number', 'options': []},
        {'key_name': 'package_quantity', 'label': '包装数量', 'data_type': 'number', 'options': []},

        # --- 电气属性 (Electrical) ---
        {'key_name': 'voltage', 'label': '电压(V)', 'data_type': 'select', 'options': ['12V', '24V', '12V/24V', '48V']}, # Updated existing likely
        {'key_name': 'power_wattage', 'label': '功率(W)', 'data_type': 'number', 'options': []},
        {'key_name': 'amperage', 'label': '电流(A)', 'data_type': 'number', 'options': []},
        {'key_name': 'resistance', 'label': '电阻(Ω)', 'data_type': 'number', 'options': []},
        {'key_name': 'frequency', 'label': '频率(Hz)', 'data_type': 'number', 'options': []},
        {'key_name': 'connector_gender', 'label': '接口公母', 'data_type': 'select', 'options': ['Male', 'Female']},
        {'key_name': 'terminal_quantity', 'label': '端子数量', 'data_type': 'number', 'options': []},
        {'key_name': 'terminal_type', 'label': '端子类型', 'data_type': 'select', 'options': ['Blade', 'Pin', 'Bullet']},
        {'key_name': 'wire_gauge', 'label': '线径(AWG)', 'data_type': 'text', 'options': []},
        {'key_name': 'wire_length', 'label': '线长(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'harness_included', 'label': '含线束', 'data_type': 'boolean', 'options': []},
        {'key_name': 'canbus_compatible', 'label': 'CANBUS兼容', 'data_type': 'boolean', 'options': []},

        # --- 照明特有属性 (Lighting) ---
        {'key_name': 'bulb_technology', 'label': '光源技术', 'data_type': 'select', 'options': ['Halogen', 'LED', 'HID/Xenon', 'Laser']},
        {'key_name': 'lumen', 'label': '光通量(lm)', 'data_type': 'number', 'options': []},
        {'key_name': 'color_temperature', 'label': '色温(K)', 'data_type': 'select', 'options': ['3000K', '4300K', '6000K', '6500K', '8000K']},
        {'key_name': 'beam_angle', 'label': '发光角度', 'data_type': 'number', 'options': []},
        {'key_name': 'beam_pattern', 'label': '光型', 'data_type': 'select', 'options': ['Low Beam', 'High Beam', 'Fog', 'Spot', 'Flood', 'Combo']},
        {'key_name': 'lifespan', 'label': '寿命(小时)', 'data_type': 'number', 'options': []},
        {'key_name': 'lens_material', 'label': '透镜材质', 'data_type': 'select', 'options': ['PC', 'Glass', 'PMMA']},
        {'key_name': 'housing_material', 'label': '外壳材质', 'data_type': 'select', 'options': ['Aluminum', 'ABS', 'Plastic', 'Steel']},
        {'key_name': 'light_function', 'label': '灯光功能', 'data_type': 'select', 'options': ['Stop', 'Tail', 'Turn', 'Reverse', 'DRL']}, # Multi-select conceptually
        {'key_name': 'certification', 'label': '认证标准', 'data_type': 'select', 'options': ['DOT', 'SAE', 'E-Mark', 'CE', 'RoHS', 'CCC']},
        {'key_name': 'waterproof_rating', 'label': '防水等级', 'data_type': 'select', 'options': ['IP65', 'IP66', 'IP67', 'IP68', 'IP69K']},

        # --- 冷却与空调 (Cooling & AC) ---
        {'key_name': 'core_material', 'label': '芯体材质', 'data_type': 'select', 'options': ['Aluminum', 'Copper', 'Brass']},
        {'key_name': 'tank_material', 'label': '水室材质', 'data_type': 'select', 'options': ['Plastic', 'Aluminum']},
        {'key_name': 'core_height', 'label': '芯体高度(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'core_width', 'label': '芯体宽度(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'core_thickness', 'label': '芯体厚度(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'inlet_diameter', 'label': '进水口径(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'outlet_diameter', 'label': '出水口径(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'row_quantity', 'label': '排数', 'data_type': 'number', 'options': []},
        {'key_name': 'refrigerant_type', 'label': '制冷剂类型', 'data_type': 'select', 'options': ['R134a', 'R1234yf']},

        # --- 制动与底盘 (Brake & Chassis) ---
        {'key_name': 'disc_diameter', 'label': '盘直径(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'disc_thickness', 'label': '盘厚度(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'bolt_hole_quantity', 'label': '螺栓孔数', 'data_type': 'number', 'options': []},
        {'key_name': 'bolt_pattern', 'label': '孔距(PCD)', 'data_type': 'text', 'options': []},
        {'key_name': 'center_bore_diameter', 'label': '中心孔径(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'piston_diameter', 'label': '活塞直径(mm)', 'data_type': 'number', 'options': []},
        {'key_name': 'piston_quantity', 'label': '活塞数量', 'data_type': 'number', 'options': []},
        {'key_name': 'pad_material', 'label': '摩擦片材质', 'data_type': 'select', 'options': ['Ceramic', 'Semi-Metallic', 'Organic']},
        {'key_name': 'sensor_included', 'label': '含传感器', 'data_type': 'boolean', 'options': []},
        
        # --- 发动机与传动 (Engine & Transmission) ---
        {'key_name': 'displacement', 'label': '排量(L)', 'data_type': 'number', 'options': []},
        {'key_name': 'cylinder_quantity', 'label': '气缸数', 'data_type': 'number', 'options': []},
        {'key_name': 'fuel_type', 'label': '燃油类型', 'data_type': 'select', 'options': ['Gasoline', 'Diesel', 'Hybrid', 'Electric']},
        {'key_name': 'drive_type', 'label': '驱动方式', 'data_type': 'select', 'options': ['FWD', 'RWD', 'AWD', '4WD']},
        {'key_name': 'transmission_type', 'label': '变速箱类型', 'data_type': 'select', 'options': ['Automatic', 'Manual', 'CVT', 'DCT']},
        {'key_name': 'gear_quantity', 'label': '档位数', 'data_type': 'number', 'options': []},
        {'key_name': 'bearing_type', 'label': '轴承类型', 'data_type': 'text', 'options': []},
        {'key_name': 'gasket_material', 'label': '垫片材质', 'data_type': 'select', 'options': ['Rubber', 'Cork', 'Metal', 'Composite']},

        # --- 车身与内饰 (Body & Interior) ---
        {'key_name': 'mirror_adjustment', 'label': '镜面调节', 'data_type': 'select', 'options': ['Manual', 'Electric', 'Heated', 'Folding']},
        {'key_name': 'glass_type', 'label': '玻璃类型', 'data_type': 'select', 'options': ['Tempered', 'Laminated']},
        {'key_name': 'tint_color', 'label': '色调', 'data_type': 'text', 'options': []},
        {'key_name': 'upholstery_material', 'label': '面料材质', 'data_type': 'select', 'options': ['Leather', 'Fabric', 'Vinyl']},
        {'key_name': 'handle_type', 'label': '把手类型', 'data_type': 'text', 'options': []},
        {'key_name': 'lock_mechanism', 'label': '锁具类型', 'data_type': 'text', 'options': []},

        # --- 商业属性 (Commercial) ---
        {'key_name': 'warranty', 'label': '质保期', 'data_type': 'select', 'options': ['1 Year', '2 Years', '3 Years', 'Lifetime']},
        {'key_name': 'country_of_origin', 'label': '原产国', 'data_type': 'select', 'options': ['China', 'Taiwan', 'Germany', 'Japan', 'USA']},
        {'key_name': 'moq', 'label': '最小起订量', 'data_type': 'number', 'options': []},
        {'key_name': 'lead_time', 'label': '交货周期(天)', 'data_type': 'number', 'options': []},
    ]

    attr_map = {}
    for ad in attrs_data:
        attr = db.session.query(AttributeDefinition).filter_by(key_name=ad['key_name']).first()
        if not attr:
            attr = AttributeDefinition(**ad)
            db.session.add(attr)
            logger.info(f"创建属性定义: {ad['label']}")
        else:
            attr.label = ad['label']
            attr.data_type = ad['data_type']
            attr.options = ad['options']
        db.session.flush()
        attr_map[ad['key_name']] = attr

    # 关联属性到分类
    # 前大灯 (10101) -> Voltage, Bulb Type, Lens Color (NEW), Bulbs Included (NEW)
    # 尾灯 (10102) -> Voltage, Color, Lens Color (NEW)
    # 保险杠 (20101) -> Material, Color
    # 叶子板 (20102) -> Material, Color
    
    def link_attrs(cat_name, attr_keys):
        cat = category_map.get(cat_name)
        if not cat:
            logger.warning(f"Category {cat_name} not found in map")
            return
            
        for idx, key in enumerate(attr_keys):
            attr = attr_map.get(key)
            if attr:
                exists = db.session.query(CategoryAttribute).filter_by(category_id=cat.id, attribute_id=attr.id).first()
                if not exists:
                    # First attribute is required for demo
                    is_req = (idx == 0)
                    # Use idx for display_order
                    link = CategoryAttribute(category_id=cat.id, attribute_id=attr.id, is_required=is_req, display_order=idx)
                    db.session.add(link)
                    logger.info(f"关联属性 {attr.label} 到 {cat_name}")
                else:
                    # update order just in case
                    exists.display_order = idx

    link_attrs('前大灯', ['voltage', 'bulb_type', 'lens_color', 'bulbs_included'])
    link_attrs('尾灯', ['voltage', 'color', 'lens_color'])
    link_attrs('保险杠', ['material', 'color'])
    link_attrs('叶子板', ['material', 'color'])

    db.session.commit()
    logger.info("商品基础数据初始化完成")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_products()
