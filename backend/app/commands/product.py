import click
import random
import re
from faker import Faker
from flask.cli import AppGroup
from app.extensions import db

product_cli = AppGroup('product')

@click.command('seed-vehicles')
@click.option('--clear', is_flag=True, help='清除现有数据')
def seed_vehicles_cmd(clear):
    """生成汽车层级数据 (真实数据: VW, BMW, Benz, Toyota)"""
    print("🚀 Starting seed-vehicles command...")
    from app.models.product import ProductVehicle
    
    # 真实参考数据 (基于 vehicle_reference_data.csv)
    # 结构: Make -> Model -> Platform (Optional) -> Default Years
    # 必须显式指定 level_type: make, model, platform, year
    reference_data = [
        # 1. Volkswagen (Code: 01)
        {
            "name": "Volkswagen", "code": "01", "level_type": "make",
            "children": [
                {"name": "Amarok", "code": "01", "level_type": "model", "years": [str(y) for y in range(2010, 2023)]}, # 2010-2022
                {"name": "Arteon", "code": "02", "level_type": "model", "years": [str(y) for y in range(2017, 2024)]}, # 2017-2023
                {"name": "Atlas", "code": "03", "level_type": "model", "years": [str(y) for y in range(2017, 2024)]}, # 2017-2023
                {"name": "Beetle", "code": "04", "level_type": "model", "years": [str(y) for y in range(2011, 2020)]}, # 2011-2019
                {"name": "Bora", "code": "05", "level_type": "model", "years": [str(y) for y in range(1998, 2006)]}, # 1998-2005
                {"name": "Caddy", "code": "06", "level_type": "model", "years": [str(y) for y in range(2003, 2021)]}, # 2003-2020
                {"name": "CC", "code": "07", "level_type": "model", "years": [str(y) for y in range(2008, 2018)]}, # 2008-2017
                {
                    "name": "Golf", "code": "08", "level_type": "model",
                    "children": [
                         {"name": "Mk4", "code": "01", "level_type": "platform", "years": [str(y) for y in range(1997, 2004)]}, # 1997-2003
                         {"name": "Mk5", "code": "02", "level_type": "platform", "years": [str(y) for y in range(2003, 2009)]}, # 2003-2008
                         {"name": "Mk6", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2008, 2013)]}, # 2008-2012
                         {"name": "Mk7", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2012, 2020)]}, # 2012-2019
                         {"name": "Mk8", "code": "05", "level_type": "platform", "years": [str(y) for y in range(2019, 2025)]}, # 2019-2024
                    ]
                },
                {"name": "ID.3", "code": "09", "level_type": "model", "years": [str(y) for y in range(2019, 2025)]}, # 2019-2024
                {"name": "ID.4", "code": "10", "level_type": "model", "years": [str(y) for y in range(2020, 2025)]}, # 2020-2024
                {
                    "name": "Jetta", "code": "11", "level_type": "model",
                    "children": [
                        {"name": "A2", "code": "01", "level_type": "platform", "years": [str(y) for y in range(1984, 1993)]},
                        {"name": "A3", "code": "02", "level_type": "platform", "years": [str(y) for y in range(1992, 2000)]},
                        {"name": "A4", "code": "03", "level_type": "platform", "years": [str(y) for y in range(1999, 2006)]},
                        {"name": "A5", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2005, 2012)]},
                        {"name": "A6", "code": "05", "level_type": "platform", "years": [str(y) for y in range(2011, 2019)]},
                        {"name": "A7", "code": "06", "level_type": "platform", "years": [str(y) for y in range(2018, 2025)]}
                    ]
                }
            ]
        },
        # 2. BMW (Code: 02)
        {
            "name": "BMW", "code": "02", "level_type": "make",
            "children": [
                {
                    "name": "1-Series", "code": "01", "level_type": "model",
                    "children": [
                        {"name": "E81", "code": "01", "level_type": "platform", "years": [str(y) for y in range(2004, 2012)]},
                        {"name": "E82", "code": "02", "level_type": "platform", "years": [str(y) for y in range(2007, 2014)]},
                        {"name": "E87", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2004, 2012)]},
                        {"name": "E88", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2007, 2014)]},
                        {"name": "F20", "code": "05", "level_type": "platform", "years": [str(y) for y in range(2011, 2020)]},
                        {"name": "F21", "code": "06", "level_type": "platform", "years": [str(y) for y in range(2011, 2020)]},
                        {"name": "F40", "code": "07", "level_type": "platform", "years": [str(y) for y in range(2019, 2025)]}
                    ]
                },
                {
                    "name": "3-Series", "code": "03", "level_type": "model",
                    "children": [
                        {"name": "E36", "code": "01", "level_type": "platform", "years": [str(y) for y in range(1990, 2001)]},
                        {"name": "E46", "code": "02", "level_type": "platform", "years": [str(y) for y in range(1998, 2007)]},
                        {"name": "E90", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2005, 2012)]},
                        {"name": "E91", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2005, 2013)]},
                        {"name": "E92", "code": "05", "level_type": "platform", "years": [str(y) for y in range(2006, 2014)]},
                        {"name": "E93", "code": "06", "level_type": "platform", "years": [str(y) for y in range(2007, 2014)]},
                        {"name": "F30", "code": "07", "level_type": "platform", "years": [str(y) for y in range(2011, 2019)]},
                        {"name": "F31", "code": "08", "level_type": "platform", "years": [str(y) for y in range(2012, 2020)]},
                        {"name": "F34", "code": "09", "level_type": "platform", "years": [str(y) for y in range(2013, 2021)]},
                        {"name": "F35", "code": "10", "level_type": "platform", "years": [str(y) for y in range(2012, 2020)]},
                        {"name": "G20", "code": "11", "level_type": "platform", "years": [str(y) for y in range(2018, 2025)]},
                        {"name": "G21", "code": "12", "level_type": "platform", "years": [str(y) for y in range(2019, 2025)]}
                    ]
                },
                {
                    "name": "5-Series", "code": "05", "level_type": "model",
                    "children": [
                        {"name": "E39", "code": "01", "level_type": "platform", "years": [str(y) for y in range(1995, 2005)]},
                        {"name": "E60", "code": "02", "level_type": "platform", "years": [str(y) for y in range(2003, 2011)]},
                        {"name": "E61", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2004, 2011)]},
                        {"name": "F10", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2010, 2018)]},
                        {"name": "F11", "code": "05", "level_type": "platform", "years": [str(y) for y in range(2010, 2018)]},
                        {"name": "G30", "code": "06", "level_type": "platform", "years": [str(y) for y in range(2017, 2024)]},
                        {"name": "G31", "code": "07", "level_type": "platform", "years": [str(y) for y in range(2017, 2024)]}
                    ]
                }
            ]  
        },
        # 3. Mercedes-Benz (Code: 03)
        {
            "name": "Mercedes-Benz", "code": "03", "level_type": "make",
            "children": [
                {
                    "name": "C-Class", "code": "04", "level_type": "model",
                    "children": [
                        {"name": "W202", "code": "01", "level_type": "platform", "years": [str(y) for y in range(1993, 2001)]},
                        {"name": "W203", "code": "02", "level_type": "platform", "years": [str(y) for y in range(2000, 2008)]},
                        {"name": "W204", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2007, 2015)]},
                        {"name": "W205", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2014, 2022)]},
                        {"name": "W206", "code": "05", "level_type": "platform", "years": [str(y) for y in range(2021, 2025)]}
                    ]
                },
                {
                    "name": "E-Class", "code": "07", "level_type": "model",
                    "children": [
                        {"name": "W210", "code": "01", "level_type": "platform", "years": [str(y) for y in range(1995, 2003)]},
                        {"name": "W211", "code": "02", "level_type": "platform", "years": [str(y) for y in range(2002, 2010)]},
                        {"name": "W212", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2009, 2017)]},
                        {"name": "W213", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2016, 2024)]}
                    ]
                },
                {
                    "name": "GLC", "code": "11", "level_type": "model",
                    "children": [
                        {"name": "X253", "code": "01", "level_type": "platform", "years": [str(y) for y in range(2015, 2023)]},
                        {"name": "C253", "code": "02", "level_type": "platform", "years": [str(y) for y in range(2016, 2023)]},
                        {"name": "X254", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2022, 2025)]}
                    ]
                }
            ]
        },
        # 4. Toyota (Code: 12)
        {
            "name": "Toyota", "code": "12", "level_type": "make",
            "children": [
                {
                    "name": "Camry", "code": "07", "level_type": "model",
                    "children": [
                        {"name": "XV30", "code": "01", "level_type": "platform", "years": [str(y) for y in range(2001, 2007)]},
                        {"name": "XV40", "code": "02", "level_type": "platform", "years": [str(y) for y in range(2006, 2012)]},
                        {"name": "XV50", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2011, 2018)]},
                        {"name": "XV70", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2017, 2025)]}
                    ]
                },
                {
                    "name": "Corolla", "code": "09", "level_type": "model",
                    "children": [
                        {"name": "E120", "code": "01", "level_type": "platform", "years": [str(y) for y in range(2000, 2007)]},
                        {"name": "E140", "code": "02", "level_type": "platform", "years": [str(y) for y in range(2006, 2014)]},
                        {"name": "E170", "code": "03", "level_type": "platform", "years": [str(y) for y in range(2013, 2020)]},
                        {"name": "E210", "code": "04", "level_type": "platform", "years": [str(y) for y in range(2018, 2025)]}
                    ]
                }
            ]
        }
    ]

    if clear:
            db.session.query(ProductVehicle).delete()
            db.session.commit()
            click.echo("✅ 已清除汽车层级数据")

    def create_nodes(nodes, parent_id=None, parent_code=""):
        for i, node in enumerate(nodes):
            current_code = node.get('code')
            
            # 1. 确定 Current Short Code
            if not current_code:
                # 如果没有提供代码（如年份），自动生成两位数序号
                current_code = f"{i+1:02d}"
            
            # 2. 确定 Full Code (用于存储和层级关联)
            if parent_code:
                # 如果有父级，拼接父级代码
                full_code = parent_code + current_code
            else:
                # 顶级节点
                full_code = current_code

            # 检查是否存在
            existing = db.session.query(ProductVehicle).filter_by(
                name=node['name'], 
                level_type=node.get('level_type', 'year'), # Default to year if not specified
                parent_id=parent_id
            ).first()
            
            # 生成 abbreviation (大写前3位，或手动指定)
            # 规则优化: 
            # 1. 移除空格和逗号等非法字符
            # 2. 特殊处理 Series -> SER
            name_upper = node.get('name').upper()
            
            if node.get('name').startswith('ID.'): 
                raw_abbr = node.get('name') # Keep ID.3
            elif 'SERIES' in name_upper:
                # 1-Series -> 1SER
                raw_abbr = name_upper.replace('SERIES', 'SER').replace('-', '').replace(' ', '')
            elif 'CLASS' in name_upper:
                # C-Class -> C-CL -> CCL ? Or just C
                # Let's try: C-Class -> CCL
                raw_abbr = name_upper.replace('CLASS', 'CL').replace('-', '').replace(' ', '')
            elif node.get('level_type') == 'year': 
                raw_abbr = node.get('name')[-2:] # Year '23'
            else:
                # Default: Remove special chars, take first 3
                clean_name = re.sub(r'[\s\-\,\.]', '', name_upper)
                raw_abbr = clean_name[:3]
            
            # Final Sanitize (just in case)
            abbr = re.sub(r'[\s,]', '', raw_abbr)

            if not existing:
                v = ProductVehicle(
                    name=node['name'],
                    abbreviation=abbr,
                    code=full_code,
                    level_type=node.get('level_type', 'year'),
                    parent_id=parent_id,
                    sort_order=(i + 1) * 10
                )
                db.session.add(v)
                db.session.flush() # 获取ID
                v_id = v.id
                click.echo(f"Created {node.get('level_type', 'year')}: {node['name']} ({full_code})")
            else:
                v_id = existing.id
                # 更新 code 如果为空
                if not existing.code:
                    existing.code = full_code
                    db.session.add(existing)
            
            # 处理 Children (递归)
            if node.get('children'):
                create_nodes(node['children'], v_id, full_code)
            
            # 处理 Years 简写列表 (转换为 Children 节点)
            if node.get('years'):
                year_nodes = []
                for idx, year_name in enumerate(node['years']):
                    year_nodes.append({
                        "name": year_name,
                        "level_type": "year",
                        # code will be generated automatically in recursive call as 01, 02...
                    })
                create_nodes(year_nodes, v_id, full_code)

    try:
        create_nodes(reference_data)
        db.session.commit()
        click.echo("✅ 汽车层级数据生成完成！(Based on Standard CSV Data)")
    except Exception as e:
        db.session.rollback()
        click.echo(f"生成失败: {e}")

@click.command('seed-categories')
@click.option('--clear', is_flag=True, help='清除现有数据')
def seed_categories_cmd(clear):
    """生成产品分类数据 (V2.0 With Schema)"""
    from app.models.product import Category, AttributeDefinition, CategoryAttribute
    
    # 1. 预定义属性 (Attributes)
    attributes_data = [
        {
            'key': 'color', 
            'label': '颜色', 
            'name_en': 'Color',
            'type': 'select', 
            'code_weight': 30, 
            'include_in_code': True, 
            'group_name': '外观属性',
            'description': '产品的外观颜色',
            'allow_custom': False,
            'options': [
                {'label': '黑色', 'value': 'Black', 'code': 'BK'}, 
                {'label': '电镀', 'value': 'Chrome', 'code': 'CH'}, 
                {'label': '红色', 'value': 'Red', 'code': 'RD'}, 
                {'label': '熏黑', 'value': 'Smoked', 'code': 'SM'}
            ]
        },
        {
            'key': 'position', 
            'label': '位置', 
            'name_en': 'Position',
            'type': 'select', 
            'code_weight': 20, 
            'include_in_code': True, 
            'group_name': '规格参数',
            'description': '安装位置',
            'allow_custom': False,
            'options': [
                {'label': '左侧', 'value': 'Left', 'code': 'L'}, 
                {'label': '右侧', 'value': 'Right', 'code': 'R'}, 
                {'label': '一对', 'value': 'Pair', 'code': '2P'}
            ]
        },
        {
            'key': 'voltage', 
            'label': '电压', 
            'name_en': 'Voltage',
            'type': 'select', 
            'code_weight': 40, 
            'include_in_code': True, 
            'group_name': '技术参数',
            'description': '工作电压',
            'allow_custom': True,
            'options': [
                {'label': '12V', 'value': '12V', 'code': '12V'}, 
                {'label': '24V', 'value': '24V', 'code': '24V'}
            ]
        },
        {
            'key': 'material', 
            'label': '材质', 
            'name_en': 'Material',
            'type': 'text', 
            'code_weight': 50, 
            'include_in_code': False,
            'group_name': '材质信息',
            'description': '主要材质',
            'allow_custom': False
        } 
    ]
    
    # 2. 预定义分类 (Tree Structure)
    categories_data = [
        # --- 1. 汽车零部件 ---
        {
            'name': '汽车零部件', 'name_en': 'Automotive Parts', 'code': '100', 'abbreviation': 'AP', 'business_type': 'vehicle',
            'description': '所有汽车相关的零部件和配件', 'icon': 'mdi:car-cog',
            'children': [
                {
                    'name': '照明系统', 'name_en': 'Lighting System', 'code': '110', 'abbreviation': 'LGT',
                    'description': '车辆照明和信号灯具', 'icon': 'mdi:car-light-high',
                    'children': [
                        {
                            'name': '前照灯', 'name_en': 'Headlights', 'code': '111', 'abbreviation': 'HL',
                            'description': '汽车前大灯总成', 'icon': 'mdi:car-light-dimmed',
                            # Config 1: Full Detail (Make, Model, Platform, Year)
                            'spu_config': { 
                                "template": "{cat}-{make}-{model}-{platform}-{year}", 
                                "vehicle_link": { "enabled": True, "levels": ["make", "model", "platform", "year"] } 
                            },
                            'bind_attrs': [
                                {'key': 'voltage', 'attribute_scope': 'spu'}, 
                                {'key': 'position', 'attribute_scope': 'sku'} # 位置通常区分左右SKU
                            ],
                            'children': [
                                {'name': 'LED前照灯', 'name_en': 'LED Headlights', 'code': '111', 'abbreviation': 'HL-LED', 'description': 'LED光源前照灯', 'icon': 'mdi:led-on'},
                                {'name': '卤素前照灯', 'name_en': 'Halogen Headlights', 'code': '111', 'abbreviation': 'HL-HAL', 'description': '传统卤素光源前照灯', 'icon': 'mdi:lightbulb'}
                            ]
                        },
                        {
                            'name': '尾灯', 'name_en': 'Tail Lights', 'code': '112', 'abbreviation': 'TL',
                            'description': '汽车尾灯总成', 'icon': 'mdi:car-brake-light',
                            # Config 2: Standard (Make, Model, Year) - Ignores Platform in Code
                            'spu_config': { 
                                "template": "{cat}-{make}-{model}-{year}", 
                                "vehicle_link": { "enabled": True, "levels": ["make", "model", "year"] } 
                            },
                            'bind_attrs': [{'key': 'position', 'attribute_scope': 'sku'}]
                        },
                        {
                            'name': '雾灯', 'name_en': 'Fog Lights', 'code': '113', 'abbreviation': 'FL', 
                            'description': '雾天行驶辅助灯', 'icon': 'mdi:weather-fog', 
                            'bind_attrs': [{'key': 'position', 'attribute_scope': 'sku'}],
                            # Config 3: Simple (Make, Year) - For universal-ish parts
                            'spu_config': { 
                                "template": "{cat}-{make}-{year}", 
                                "vehicle_link": { "enabled": True, "levels": ["make", "year"] } 
                            }
                        }
                    ]
                },
                {
                    'name': '发动机系统', 'name_en': 'Engine System', 'code': '120', 'abbreviation': 'ENG',
                    'description': '发动机及其周边系统', 'icon': 'mdi:engine',
                    'children': [
                        {
                            'name': '滤清器', 'name_en': 'Filters', 'code': '121', 'abbreviation': 'FIL',
                            'description': '各类滤清器', 'icon': 'mdi:air-filter',
                            'spu_config': { "template": "{cat}-{make}-{model}-{year}", "vehicle_link": { "enabled": True, "levels": ["make", "model", "year"] } },
                            'children': [
                                {'name': '机油滤清器', 'name_en': 'Oil Filters', 'code': '121', 'abbreviation': 'OIL-FIL', 'description': '机油过滤', 'icon': 'mdi:oil'},
                                {'name': '空气滤清器', 'name_en': 'Air Filters', 'code': '121', 'abbreviation': 'AIR-FIL', 'description': '空气过滤', 'icon': 'mdi:air-filter'}
                            ]
                        },
                        {
                            'name': '点火系统', 'name_en': 'Ignition', 'code': '122', 'abbreviation': 'IGN',
                            'description': '点火线圈与火花塞', 'icon': 'mdi:fire',
                            'children': [
                                {'name': '火花塞', 'name_en': 'Spark Plugs', 'code': '122', 'abbreviation': 'SPK', 'description': '点火火花塞', 'icon': 'mdi:spark'}
                            ]
                        }
                    ]
                },
                {
                    'name': '制动系统', 'name_en': 'Brake System', 'code': '130', 'abbreviation': 'BRK',
                    'description': '刹车制动相关部件', 'icon': 'mdi:car-brake-abs',
                    'children': [
                        {
                            'name': '刹车片', 'name_en': 'Brake Pads', 'code': '131', 'abbreviation': 'PD',
                            'description': '刹车片/摩擦片', 'icon': 'mdi:disc-player', 
                            'spu_config': { "template": "{cat}-{make}-{model}-{year}", "vehicle_link": { "enabled": True, "levels": ["make", "model", "year"] } },
                            'bind_attrs': [{'key': 'position', 'attribute_scope': 'sku'}, {'key': 'material', 'attribute_scope': 'spu'}]
                        },
                        {'name': '刹车盘', 'name_en': 'Brake Discs', 'code': '132', 'abbreviation': 'DSC', 'description': '刹车盘/制动盘', 'icon': 'mdi:disc', 'bind_attrs': [{'key': 'position', 'attribute_scope': 'sku'}, {'key': 'material', 'attribute_scope': 'spu'}]}
                    ]
                }
            ]
        },
        # --- 2. 工业管路 (非汽配) ---
        {
            'name': '工业管路', 'name_en': 'Industrial Piping', 'code': '200', 'abbreviation': 'IND', 'business_type': 'general',
            'description': '工业用管道、阀门及配件', 'icon': 'mdi:pipe',
            'children': [
                {
                    'name': '阀门', 'name_en': 'Valves', 'code': '210', 'abbreviation': 'VLV',
                    'description': '流体控制阀门', 'icon': 'mdi:valve',
                    'children': [
                        {
                            'name': '球阀', 'name_en': 'Ball Valves', 'code': '211', 'abbreviation': 'BAL',
                            'description': '球体控制阀门', 'icon': 'mdi:valve-open',
                            'spu_config': { "template": "{cat}-{series}-{spec}", "fields": [{"key": "series", "type": "input", "label": "系列"}, {"key": "spec", "type": "input", "label": "规格"}] },
                            'bind_attrs': [{'key': 'material', 'attribute_scope': 'spu'}],
                            'children': [
                                {'name': '不锈钢球阀', 'name_en': 'SS Ball Valve', 'code': '211', 'abbreviation': 'BAL-SS', 'description': '304/316不锈钢球阀', 'icon': 'mdi:valve'},
                                {'name': '铜球阀', 'name_en': 'Brass Ball Valve', 'code': '211', 'abbreviation': 'BAL-BR', 'description': '黄铜球阀', 'icon': 'mdi:valve'}
                            ]
                        },
                        {'name': '蝶阀', 'name_en': 'Butterfly Valves', 'code': '212', 'abbreviation': 'BUT', 'description': '蝶式阀门', 'icon': 'mdi:butterfly', 'bind_attrs': [{'key': 'material', 'attribute_scope': 'spu'}]},
                        {'name': '闸阀', 'name_en': 'Gate Valves', 'code': '213', 'abbreviation': 'GAT', 'description': '闸板阀门', 'icon': 'mdi:gate', 'bind_attrs': [{'key': 'material', 'attribute_scope': 'spu'}]}
                    ]
                },
                {
                    'name': '管件', 'name_en': 'Fittings', 'code': '220', 'abbreviation': 'FIT',
                    'description': '管道连接件', 'icon': 'mdi:pipe-disconnected',
                    'children': [
                        {'name': '弯头', 'name_en': 'Elbows', 'code': '221', 'abbreviation': 'ELB', 'description': '90度/45度弯头', 'icon': 'mdi:angle-right', 'bind_attrs': [{'key': 'material', 'attribute_scope': 'spu'}]},
                        {'name': '三通', 'name_en': 'Tees', 'code': '222', 'abbreviation': 'TEE', 'description': 'T型三通', 'icon': 'mdi:source-branch', 'bind_attrs': [{'key': 'material', 'attribute_scope': 'spu'}]}
                    ]
                }
            ]
        },
        # --- 3. 五金工具 ---
        {
            'name': '五金工具', 'name_en': 'Hardware Tools', 'code': '300', 'abbreviation': 'TOOL', 'business_type': 'general',
            'description': '各类手动及电动工具', 'icon': 'mdi:tools',
            'children': [
                {
                    'name': '手动工具', 'name_en': 'Hand Tools', 'code': '310', 'abbreviation': 'HAND',
                    'description': '非电动手动工具', 'icon': 'mdi:hammer',
                    'children': [
                        {
                            'name': '扳手', 'name_en': 'Wrenches', 'code': '311', 'abbreviation': 'WR',
                            'description': '各种规格扳手', 'icon': 'mdi:wrench',
                            'spu_config': { "template": "{cat}-{series}", "fields": [{"key": "series", "type": "input", "label": "系列"}] },
                            'bind_attrs': [{'key': 'material', 'attribute_scope': 'spu'}]
                        },
                        {'name': '螺丝刀', 'name_en': 'Screwdrivers', 'code': '312', 'abbreviation': 'SCR', 'description': '一字/十字螺丝刀', 'icon': 'mdi:screw-driver', 'bind_attrs': [{'key': 'material', 'attribute_scope': 'spu'}]}
                    ]
                },
                {
                    'name': '电动工具', 'name_en': 'Power Tools', 'code': '320', 'abbreviation': 'PWR',
                    'description': '电力驱动工具', 'icon': 'mdi:power-plug',
                    'children': [
                        {'name': '电钻', 'name_en': 'Drills', 'code': '321', 'abbreviation': 'DRL', 'description': '手持电钻', 'icon': 'mdi:drill', 'bind_attrs': [{'key': 'voltage', 'attribute_scope': 'spu'}]}
                    ]
                }
            ]
        }
    ]

    if clear:
        click.echo("正在清除现有分类及属性数据...")
        try:
            # Clear dependent tables first
            db.session.query(CategoryAttribute).delete()
            # Clear Attributes
            db.session.query(AttributeDefinition).delete()
            
            # Handle products dependency: Set category_id to NULL
            from app.models.product import Product, sku_suffix_categories
            db.session.query(Product).update({Product.category_id: None})
            
            # Handle sku_suffix_categories dependency
            db.session.execute(sku_suffix_categories.delete())
            
            db.session.query(Category).delete()
            db.session.commit()
            click.echo("✅ 已清除分类数据")
        except Exception as e:
            db.session.rollback()
            click.echo(f"清除失败 (可能有外键约束): {e}")
            return

    # Step 1: Create Attributes
    attr_map = {}
    for attr_data in attributes_data:
        attr = AttributeDefinition(
            key_name=attr_data['key'],
            label=attr_data['label'],
            data_type=attr_data['type'],
            code_weight=attr_data.get('code_weight', 99),
            include_in_code=attr_data.get('include_in_code', True),
            options=attr_data.get('options'),
            name_en=attr_data.get('name_en'),
            group_name=attr_data.get('group_name'),
            description=attr_data.get('description'),
            allow_custom=attr_data.get('allow_custom', False)
        )
        db.session.add(attr)
        db.session.flush()
        attr_map[attr.key_name] = attr
        
    # Step 2: Create Categories
    def create_recursive(data, parent_id=None, level=1):
        for i, item in enumerate(data):
            cat = Category(
                name=item['name'],
                name_en=item.get('name_en'),
                code=item['code'],
                abbreviation=item.get('abbreviation') or item['code'], # Default abbr to code
                business_type=item.get('business_type', 'vehicle'),
                description=item.get('description'),
                icon=item.get('icon'),
                spu_config=item.get('spu_config'),
                sort_order=(i + 1) * 10,
                parent_id=parent_id,
                level=level, # Auto populate level
                is_leaf=not item.get('children')
            )
            db.session.add(cat)
            db.session.flush() # Commit to get ID
            
            # Bind Attributes
            if item.get('bind_attrs'):
                for attr_item in item['bind_attrs']:
                    # 支持 {'key': 'x', 'include_in_code': False, 'attribute_scope': 'sku'} 或 'x'
                    attr_key = attr_item
                    override_code = None
                    attr_scope = 'spu'
                    
                    if isinstance(attr_item, dict):
                        attr_key = attr_item['key']
                        override_code = attr_item.get('include_in_code')
                        attr_scope = attr_item.get('attribute_scope', 'spu')
                        
                    if attr_key in attr_map:
                        mapping = CategoryAttribute(
                            category_id=cat.id,
                            attribute_id=attr_map[attr_key].id,
                            is_required=False,
                            display_order=0,
                            include_in_code=override_code, # Set override
                            attribute_scope=attr_scope # Set scope
                        )
                        db.session.add(mapping)
            
            if item.get('children'):
                cat.is_leaf = False
                create_recursive(item['children'], cat.id, level + 1)

    try:
        create_recursive(categories_data)
        db.session.commit()
        click.echo("✅ 产品分类及属性数据生成完成！")
    except Exception as e:
        db.session.rollback()
        click.echo(f"生成失败: {e}")

@click.command('fix-categories')
def fix_categories_cmd():
    """修复 Category 表的 level 和 abbreviation 数据"""
    from app.models.product import Category
    
    click.echo("开始修复 Category 数据...")
    
    # 1. 递归修复 Level
    def fix_level_recursive(parent_id=None, level=1):
        if parent_id is None:
            cats = db.session.query(Category).filter(Category.parent_id.is_(None)).all()
        else:
            cats = db.session.query(Category).filter(Category.parent_id == parent_id).all()
        
        for cat in cats:
            cat.level = level
            
            # 2. 修复 Abbreviation
            if not cat.abbreviation:
                cat.abbreviation = cat.code
                click.echo(f"Fixed abbr for {cat.name}: {cat.abbreviation}")
            
            # 递归子节点
            fix_level_recursive(cat.id, level + 1)
    
    try:
        fix_level_recursive()
        db.session.commit()
        click.echo("✅ Category 数据修复完成！")
    except Exception as e:
        db.session.rollback()
        click.echo(f"修复失败: {e}")

@click.command('seed-products')
@click.option('--count', default=100, help='生成 SPU 数量')
@click.option('--clear', is_flag=True, help='清除现有数据')
def seed_products_cmd(count, clear):
    """生成虚拟商品数据 (SPU + SKU + Codes) - V2.0 Dual Track"""
    from app.models.product import Product, ProductVariant, ProductReferenceCode, ProductFitment, ProductVehicle
    from app.models.product import Category
    
    fake_zh = Faker('zh_CN')
    
    # 1. Clear Data
    if clear:
        click.echo("正在清除现有商品数据...")
        try:
            # Clear dependents first
            db.session.query(ProductReferenceCode).delete()
            db.session.query(ProductVariant).delete()
            db.session.query(ProductFitment).delete()
            
            # Clear SPU
            db.session.query(Product).delete()
            
            db.session.commit()
            click.echo("✅ 已清除商品数据")
        except Exception as e:
            db.session.rollback()
            click.echo(f"清除失败 (可能有外键约束): {e}")
            return

    # 2. Get dependencies
    leaf_categories = db.session.query(Category).filter_by(is_leaf=True).all()
    year_nodes = db.session.query(ProductVehicle).filter_by(level_type='year').all()
    
    if not leaf_categories:
        click.echo("❌ 错误: 没有找到末级分类。请先运行 flask seed-categories")
        return

    click.echo(f"开始生成 {count} 条 SPU 数据 (V2.0)...")
    
    # 模拟的外部参考码品牌
    ref_brands = ['Toyota', 'Honda', 'BMW', 'Bosch', 'Valeo', 'Denso', 'TRW']
    
    for i in range(count):
        cat = random.choice(leaf_categories)
        spu_params = {}
        brand_name = None
        
        # --- 1. SPU Coding Logic (Feature Code Prefix) ---
        is_vehicle_part = (cat.business_type == 'vehicle' or not cat.business_type)
        vehicle_codes = {}
        
        if is_vehicle_part and year_nodes:
            # 随机模拟一个车型选择: Year -> Model -> Brand
            node_year = random.choice(year_nodes)
            node_model = node_year.parent
            if node_model and node_model.parent:
                node_brand = node_model.parent
                
                spu_params['make'] = node_brand.abbreviation
                spu_params['model'] = node_model.abbreviation
                spu_params['year'] = node_year.abbreviation
                brand_name = node_brand.name
                
                # Store full codes for SKU Generation
                # Code structure: Make(2) + Model(2)
                # Note: node.code is full path code. 
                # Brand Code = node_brand.code (2 chars)
                # Model Code = node_model.code (4 chars, includes brand) -> We just need Model part? 
                # L2.0 Spec: Vehicle Code (4 digit) = Brand(2) + Model(2)
                # Let's extract last 2 digits of model code if model code is 4 digits
                vehicle_code_str = node_model.code 
                if len(vehicle_code_str) > 4: 
                     vehicle_code_str = vehicle_code_str[:4] # Truncate if platform included
                elif len(vehicle_code_str) < 4:
                     vehicle_code_str = vehicle_code_str.ljust(4, '0')

                vehicle_codes['full'] = vehicle_code_str
        
        if not spu_params:
            spu_params['series'] = f"S{random.randint(1,9)}"
            spu_params['brand'] = "GEN"
            brand_name = "General"
            vehicle_codes['full'] = "0000" # General parts

        # SPU Feature Code (Business ID)
        template = cat.spu_config.get('template', '{cat}-{brand}-{series}') if cat.spu_config else '{cat}-{brand}-{series}'
        spu_code = template.replace('{cat}', cat.abbreviation or cat.code)
        for k, v in spu_params.items():
            spu_code = spu_code.replace(f'{{{k}}}', v)
        # 替换剩余 placeholder 并加随机数以防重复
        # 改进: 使用随机字符替换占位符，避免 'X-X' 导致的重复
        def replace_placeholder(match):
            return f"{random.randint(10, 99)}"
            
        spu_code = re.sub(r'\{.*?\}', replace_placeholder, spu_code)
        
        # 再次确保唯一性，追加随机后缀
        spu_code += f"-{random.randint(1000, 9999)}"
        
        # --- 2. Create SPU ---
        name = f"{brand_name} {cat.name} {random.choice(['总成', '套装', '组件'])}"
        
        spu = Product(
            spu_code=spu_code,
            name=name,
            category_id=cat.id,
            brand=brand_name,
            spu_coding_metadata=spu_params,
            attributes={
                "voltage": "12V",
                "material": random.choice(["ABS", "Aluminum"]),
                "warranty": "1 Year"
            },
            description=fake_zh.text(max_nb_chars=200),
            main_image=f"https://via.placeholder.com/150?text={spu_code}"
        )
        db.session.add(spu)
        db.session.flush() # Get SPU ID
        
        # --- 3. Generate Variants (Dual Track) ---
        # Variants: Left/Right (Position) or Colors
        
        variants_config = [
            {'suffix': 'L', 'pos': 'Left', 'code': 'L'},
            {'suffix': 'R', 'pos': 'Right', 'code': 'R'}
        ]
        
        # SKU Serial logic: 01, 02...
        # L2.0 Spec: [Cat(3)][Vehicle(4)][Serial(2)][Suffix]
        cat_code = cat.code.zfill(3)
        veh_code = vehicle_codes.get('full', '0000')
        serial = f"{random.randint(1, 99):02d}" # Random serial for simulation
        
        for idx, var in enumerate(variants_config):
            # 1. System SKU (Numeric + Suffix)
            # E.g. 111 + 0105 + 01 + L
            system_sku = f"{cat_code}{veh_code}{serial}{var['suffix']}"
            
            # 2. Feature Code (SPU + Attr)
            # E.g. HL-TOY-CAM-07-11 + -L
            feature_code = f"{spu_code}-{var['code']}"
            
            variant = ProductVariant(
                product_id=spu.id,
                sku=system_sku, 
                feature_code=feature_code,
                specs={
                    "quality": "Aftermarket", 
                    "position": var['pos'],
                    "supplier_sku": f"SUP-{random.randint(1000,9999)}"
                },
                quality_type="Aftermarket",
                price=round(random.uniform(50, 200), 2),
                cost_price=round(random.uniform(20, 100), 2),
                net_weight=round(random.uniform(0.5, 5.0), 2),
                gross_weight=round(random.uniform(0.6, 5.5), 2),
                pack_length=round(random.uniform(10, 50), 1),
                pack_width=round(random.uniform(10, 30), 1),
                pack_height=round(random.uniform(5, 20), 1),
                declared_name=f"{cat.name} (Auto Parts)",
                declared_unit="PCS"
            )
            db.session.add(variant)

        if (i + 1) % 10 == 0:
            db.session.commit()
            click.echo(f"已生成 {i+1}/{count} SPU...")

    db.session.commit()
    click.echo(f"✅ 成功生成 {count} 条 SPU 数据及其关联数据 (双轨制)！")

@click.command('check-db')
def check_db_cmd():
    """检查数据库中的 ProductVehicle 数据"""
    from app.models.product import ProductVehicle
    
    count = db.session.query(ProductVehicle).count()
    click.echo(f"ProductVehicle count: {count}")
    
    if count > 0:
        roots = db.session.query(ProductVehicle).filter(ProductVehicle.parent_id.is_(None)).all()
        click.echo(f"Root nodes: {[r.name for r in roots]}")

product_cli.add_command(seed_vehicles_cmd)
product_cli.add_command(seed_categories_cmd)
product_cli.add_command(fix_categories_cmd)
product_cli.add_command(seed_products_cmd)
product_cli.add_command(check_db_cmd)
