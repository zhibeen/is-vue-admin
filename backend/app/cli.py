import click
from flask.cli import with_appcontext
from sqlalchemy import select
from app.extensions import db
from app.models.category import Category, AttributeDefinition, CategoryAttribute
from app.models.vehicle import VehicleAux
from app.models.product import SkuSuffix, Product, ProductFitment
from app.models.user import User, Role, Permission
from app.services.sku_generator import generate_sku

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Populate database with initial seed data."""
    click.echo('Seeding database...')
    
    # --- AUTH SEED ---
    
    # 0. Permissions
    permissions_data = [
        ('product:create', 'Create products'),
        ('product:update', 'Update products'),
        ('product:delete', 'Delete products'),
        ('category:manage', 'Manage categories'),
        ('vehicle:manage', 'Manage vehicles'),
    ]
    
    all_permissions = []
    for name, desc in permissions_data:
        perm = db.session.scalar(select(Permission).where(Permission.name == name))
        if not perm:
            perm = Permission(name=name, description=desc)
            db.session.add(perm)
        all_permissions.append(perm)
    
    db.session.flush()

    # 1. Roles
    admin_role = Role(name='admin', description='Administrator')
    editor_role = Role(name='editor', description='Content Editor')
    
    roles = [admin_role, editor_role]
    for r in roles:
        existing = db.session.scalar(select(Role).where(Role.name == r.name))
        if not existing:
            db.session.add(r)
        else:
            if r.name == 'admin': admin_role = existing
            if r.name == 'editor': editor_role = existing
    
    # Assign Permissions to Roles
    # Admin gets ALL permissions
    for perm in all_permissions:
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
            
    # Editor gets specific permissions
    editor_perms = ['product:create', 'product:update'] # No delete
    for perm in all_permissions:
        if perm.name in editor_perms and perm not in editor_role.permissions:
            editor_role.permissions.append(perm)

    db.session.flush()

    # 2. Users
    admin_user = db.session.scalar(select(User).where(User.username == 'admin'))
    if not admin_user:
        admin_user = User(username='admin', email='admin@example.com')
        admin_user.set_password('admin123')
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)
        click.echo('Created user: admin')
    else:
        # Ensure admin has role
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)

    editor_user = db.session.scalar(select(User).where(User.username == 'editor'))
    if not editor_user:
        editor_user = User(username='editor', email='editor@example.com')
        editor_user.set_password('editor123')
        editor_user.roles.append(editor_role)
        db.session.add(editor_user)
        click.echo('Created user: editor')

    # --- PRODUCT SEED ---
    
    # 1. Sku Suffixes
    suffixes = [
        SkuSuffix(code='L', meaning_en='Left / Driver Side', meaning_cn='左侧/驾驶位'),
        SkuSuffix(code='R', meaning_en='Right / Pass. Side', meaning_cn='右侧/副驾位'),
        SkuSuffix(code='D', meaning_en='Driver Side (Legacy)', meaning_cn='驾驶位(旧)'),
        SkuSuffix(code='P', meaning_en='Pass. Side (Legacy)', meaning_cn='副驾位(旧)'),
        SkuSuffix(code='C', meaning_en='Chrome', meaning_cn='镀铬'),
        SkuSuffix(code='B', meaning_en='Black', meaning_cn='黑色'),
        SkuSuffix(code='S', meaning_en='Set / Pair', meaning_cn='套装/对'),
    ]
    for s in suffixes:
        db.session.merge(s)
    
    # 2. Global Attributes
    attrs = {
        'material': AttributeDefinition(key_name='material', label='材质', data_type='text', is_global=True),
        'voltage': AttributeDefinition(key_name='voltage', label='电压', data_type='select', options=['12V', '24V']),
        'lens_color': AttributeDefinition(key_name='lens_color', label='透镜颜色', data_type='select', options=['Clear', 'Smoke', 'Amber']),
        'housing_color': AttributeDefinition(key_name='housing_color', label='底壳颜色', data_type='text'),
        'bulbs_included': AttributeDefinition(key_name='bulbs_included', label='含灯泡', data_type='boolean'),
    }
    
    for key, attr in attrs.items():
        existing = db.session.scalar(select(AttributeDefinition).where(AttributeDefinition.key_name == key))
        if not existing:
            db.session.add(attr)
        else:
            attrs[key] = existing
    
    db.session.flush()

    # 3. Categories (Tree) - Optimized check
    def get_or_create_category(name, code=None, parent=None, is_leaf=False):
        stmt = select(Category).where(Category.name == name)
        if parent:
            stmt = stmt.where(Category.parent_id == parent.id)
        existing = db.session.scalar(stmt)
        if existing:
            return existing
        
        new_cat = Category(name=name, code=code, parent=parent, is_leaf=is_leaf)
        db.session.add(new_cat)
        db.session.flush() # flush to get ID
        return new_cat

    # Level 1
    cat_lighting = get_or_create_category('汽车照明')
    cat_body = get_or_create_category('车身覆盖件')
    
    # Level 2
    cat_headlight = get_or_create_category('前大灯', code='HDL', parent=cat_lighting)
    cat_taillight = get_or_create_category('尾灯', code='TAL', parent=cat_lighting)
    cat_bumper = get_or_create_category('保险杠', code='188', parent=cat_body)

    # Level 3
    cat_bumper_front = get_or_create_category('前保险杠', code='189', parent=cat_bumper, is_leaf=True)
    cat_bumper_rear = get_or_create_category('后保险杠', code='190', parent=cat_bumper, is_leaf=True)
    
    # 4. Bind Attributes (Check existing first to avoid PK constraint error)
    def bind_attribute(category, attr_def, order=0):
        stmt = select(CategoryAttribute).where(
            CategoryAttribute.category_id == category.id,
            CategoryAttribute.attribute_id == attr_def.id
        )
        if not db.session.scalar(stmt):
            db.session.add(CategoryAttribute(category=category, attribute_definition=attr_def, display_order=order))

    bind_attribute(cat_headlight, attrs['voltage'], 1)
    bind_attribute(cat_headlight, attrs['lens_color'], 2)
    bind_attribute(cat_headlight, attrs['bulbs_included'], 3)
    bind_attribute(cat_bumper, attrs['material'], 1)

    # 5. Vehicle Data
    def get_or_create_vehicle(name, level_type, parent=None, code=None, abbr=None):
        stmt = select(VehicleAux).where(VehicleAux.name == name, VehicleAux.level_type == level_type)
        if parent:
            stmt = stmt.where(VehicleAux.parent_id == parent.id)
        existing = db.session.scalar(stmt)
        if existing:
            # Update existing if needed (for migration)
            if code and existing.code != code: existing.code = code
            if abbr and existing.abbr != abbr: existing.abbr = abbr
            return existing
        
        v = VehicleAux(name=name, level_type=level_type, parent=parent, code=code, abbr=abbr)
        db.session.add(v)
        db.session.flush()
        return v

    # Legacy support or update
    toyota = get_or_create_vehicle('丰田 (Toyota)', 'brand', code='04', abbr='TOYOTA')
    vw = get_or_create_vehicle('大众 (Volkswagen)', 'brand', code='05', abbr='VW')
    
    # New Brands
    bmw = get_or_create_vehicle('宝马 (BMW)', 'brand', code='01', abbr='BMW')
    benz = get_or_create_vehicle('奔驰 (Mercedes)', 'brand', code='02', abbr='BENZ')
    audi = get_or_create_vehicle('奥迪 (Audi)', 'brand', code='03', abbr='AUDI')

    # Models
    camry = get_or_create_vehicle('Camry (凯美瑞)', 'model', parent=toyota)
    golf = get_or_create_vehicle('Golf (高尔夫)', 'model', parent=vw)
    
    bmw_3 = get_or_create_vehicle('3 Series (3系)', 'model', parent=bmw)
    bmw_5 = get_or_create_vehicle('5 Series (5系)', 'model', parent=bmw)
    bmw_x3 = get_or_create_vehicle('X3', 'model', parent=bmw)
    bmw_x5 = get_or_create_vehicle('X5', 'model', parent=bmw)
    
    benz_c = get_or_create_vehicle('C-Class (C级)', 'model', parent=benz)
    benz_e = get_or_create_vehicle('E-Class (E级)', 'model', parent=benz)

    # Submodels
    get_or_create_vehicle('320i', 'submodel', parent=bmw_3)
    get_or_create_vehicle('325i', 'submodel', parent=bmw_3)
    get_or_create_vehicle('330i', 'submodel', parent=bmw_3)
    
    get_or_create_vehicle('525Li', 'submodel', parent=bmw_5)
    get_or_create_vehicle('530Li', 'submodel', parent=bmw_5)

    # 6. Product Samples
    if not db.session.scalar(select(Product).where(Product.name == 'Camry 2020 Front Bumper')):
        sku = generate_sku('189', '00', None)
        p1 = Product(
            sku=sku,
            name='Camry 2020 Front Bumper',
            feature_code='BUM-TOY-CAM-20-FR',
            category=cat_bumper_front,
            attributes={'material': 'ABS Plastic'},
            length=180.0, width=50.0, height=60.0, weight=8.5
        )
        p1.fitments.append(ProductFitment(vehicle=camry, notes='Fits 2018-2022'))
        db.session.add(p1)
        click.echo(f'Created Product: {p1.name} (SKU: {sku})')

    if not db.session.scalar(select(Product).where(Product.name == 'Golf MK7 Headlight Left')):
        sku_l = generate_sku('HDL', '00', 'L')
        p2 = Product(
            sku=sku_l,
            name='Golf MK7 Headlight Left',
            feature_code='HDL-VW-GOL-15-L',
            category=cat_headlight,
            suffix_code='L',
            attributes={'voltage': '12V', 'lens_color': 'Clear', 'bulbs_included': True},
            length=60.0, width=30.0, height=25.0, weight=3.2
        )
        p2.fitments.append(ProductFitment(vehicle=golf, notes='MK7 Only'))
        db.session.add(p2)
        click.echo(f'Created Product: {p2.name} (SKU: {sku_l})')
    
    db.session.commit()
    click.echo('Database seeded successfully!')
