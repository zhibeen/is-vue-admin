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

    # Clean existing data
    click.echo('Cleaning existing data...')
    
    try:
        # Clean association tables first
        # Note: We need to access the table object directly from the model
        # User.roles is a relationship to Role, secondary is 'user_roles'
        
        # Reflect the metadata to get the table objects if not directly available
        # Or execute raw SQL for cleaning association tables which is often cleaner for seeding scripts
        
        db.session.execute(db.text("TRUNCATE TABLE user_roles CASCADE"))
        db.session.execute(db.text("TRUNCATE TABLE role_permissions CASCADE"))
        
        # Now delete main entities
        db.session.query(User).delete()
        db.session.query(Role).delete()
        db.session.query(Permission).delete()
        
        db.session.commit()
        click.echo('Existing data cleaned.')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error cleaning data: {e}')
        # Continue seeding anyway or return?
        # If truncate fails (e.g. permission denied), we might want to stop.
        # But for now let's try to continue or return.
        return
    
    # --- AUTH SEED ---
    
    # 0. Permissions
    permissions_data = [
        # System
        ('system:view', '查看系统管理'),
        ('system:user:view', '查看用户'),
        ('system:user:manage', '管理用户'),
        ('system:role:view', '查看角色'),
        ('system:role:manage', '管理角色'),
        
        # Product
        ('product:view', '查看商品列表'),
        ('product:create', '创建商品'),
        ('product:update', '更新商品'),
        ('product:delete', '删除商品'),
        ('category:manage', '分类管理'),
        ('vehicle:manage', '车型管理'),
    ]
    
    MODULE_MAP = {
        'system': '系统管理',
        'product': '商品中心',
        'category': '商品中心',
        'vehicle': '商品中心',
        'order': '订单中心',
    }
    RESOURCE_MAP = {
        'user': '用户管理',
        'role': '角色管理',
        'product': '商品列表',
        'category': '分类管理',
        'vehicle': '车型库管理',
        'system': '系统概览', # For system:view
    }

    all_permissions = []
    for name, desc in permissions_data:
        # Parse Structure
        parts = name.split(':')
        module_key = 'default'
        resource_key = 'default'
        action_key = name

        if len(parts) >= 3:
            module_key = parts[0]
            resource_key = parts[1]
            action_key = parts[2]
        elif len(parts) == 2:
            resource_key = parts[0]
            action_key = parts[1]
            if resource_key in ['product', 'category', 'vehicle']:
                module_key = 'product'
            else:
                module_key = resource_key
        
        module_val = MODULE_MAP.get(module_key, '其他功能')
        resource_val = RESOURCE_MAP.get(resource_key, resource_key)
        
        perm = db.session.scalar(select(Permission).where(Permission.name == name))
        if not perm:
            perm = Permission(
                name=name, 
                description=desc,
                module=module_val,
                resource=resource_val,
                action=action_key
            )
            db.session.add(perm)
        else:
            # Update fields
            perm.description = desc
            perm.module = module_val
            perm.resource = resource_val
            perm.action = action_key
            
        all_permissions.append(perm)
    
    db.session.flush()

    # 1. Roles
    # 建议：虽然这里将 Role.name 改为了中文以满足需求，
    # 但在生产环境中，建议 Role.name 保持英文 (如 'admin') 作为唯一标识，
    # 而使用 Role.description ('管理员') 进行前端展示。
    roles_data = [
        ('管理员', '管理员'),      # 原 admin
        ('内容编辑', '内容编辑'),   # 原 editor
        ('访客', '访客'),         # 原 viewer
        ('商品经理', '商品经理'),   # 原 product_mgr
        ('订单经理', '订单经理'),   # 原 order_mgr
    ]
    
    created_roles = []
    for r_name, r_desc in roles_data:
        role = db.session.scalar(select(Role).where(Role.name == r_name))
        if not role:
            role = Role(name=r_name, description=r_desc)
            db.session.add(role)
        else:
            # Update description if needed
            if role.description != r_desc:
                role.description = r_desc
        created_roles.append(role)
        
    db.session.flush()
    
    # Assign Permissions to Roles
    # Admin gets all
    admin_role = next(r for r in created_roles if r.name == '管理员')
    admin_role.permissions = all_permissions
    
    # Editor gets product permissions
    editor_role = next(r for r in created_roles if r.name == '内容编辑')
    product_perms = [p for p in all_permissions if 'product' in p.name]
    editor_role.permissions = product_perms

    db.session.commit()

    # 2. Users
    # 创建一个登录名为 'admin' 的用户，分配 '管理员' 角色
    if not db.session.scalar(select(User).where(User.username == 'admin')):
        user = User(username='admin', email='admin@example.com')
        user.set_password('password')
        user.roles = [admin_role]
        db.session.add(user)
        
    # 创建一个登录名为 'editor' 的用户，分配 '内容编辑' 角色
    if not db.session.scalar(select(User).where(User.username == 'editor')):
        user = User(username='editor', email='editor@example.com')
        user.set_password('password')
        user.roles = [editor_role]
        db.session.add(user)

    # 3. Create 20 Fake Users
    import random
    
    fake_surnames = ['赵', '钱', '孙', '李', '周', '吴', '郑', '王', '冯', '陈', '褚', '卫', '蒋', '沈', '韩', '杨']
    fake_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟', '涛']
    
    for i in range(1, 21):
        u_name = f'user{i}'
        if not db.session.scalar(select(User).where(User.username == u_name)):
            # Generate fake Chinese name
            cn_name = random.choice(fake_surnames) + random.choice(fake_names)
            
            user = User(
                username=u_name,
                email=f'{u_name}@example.com',
                nickname=cn_name
            )
            user.set_password('password')
            
            # Randomly assign a role (excluding admin to keep it special)
            # Weighted choice: mostly viewers/editors
            role_choice = random.choices(
                population=[
                    next(r for r in created_roles if r.name == '访客'),
                    next(r for r in created_roles if r.name == '内容编辑'),
                    next(r for r in created_roles if r.name == '商品经理'),
                    next(r for r in created_roles if r.name == '订单经理')
                ],
                weights=[40, 30, 15, 15],
                k=1
            )[0]
            
            user.roles = [role_choice]
            db.session.add(user)

    db.session.commit()
    click.echo('Database seeded with 20 fake users!')

    # --- DATA PERMISSION SEED ---
    from app.models.data_permission import DataPermissionMeta
    click.echo('Seeding Data Permission Metas...')

    # Helper to create/update meta
    def create_meta(key, label, type, parent=None, desc=None, sort=0):
        meta = db.session.scalar(select(DataPermissionMeta).where(DataPermissionMeta.key == key))
        if not meta:
            meta = DataPermissionMeta(key=key, label=label, type=type, parent=parent, description=desc, sort_order=sort)
            db.session.add(meta)
            db.session.flush() # flush to get ID for children
        return meta

    # L1: SKU数据权限
    sku_cat = create_meta(
        'sku', 'SKU数据权限', 'category', 
        desc='SKU权限人请前往产品-产品管理模块进行分配SKU权限人，SKU权限人包括：开发人、采购员、产品负责人'
    )

    # L2: 产品
    prod_mod = create_meta('sku:product_mod', '产品', 'module', parent=sku_cat, sort=10)
    # L3: 产品管理
    create_meta('sku:product:manage', '产品管理/捆绑产品', 'resource', parent=prod_mod, sort=1)
    
    # L2: 仓库
    wh_mod = create_meta('sku:warehouse_mod', '仓库', 'module', parent=sku_cat, sort=20)
    # L3: 资源
    create_meta('sku:warehouse:stock', '库存明细', 'resource', parent=wh_mod, sort=1)
    create_meta('sku:warehouse:flow', '库存流水', 'resource', parent=wh_mod, sort=2)
    create_meta('sku:warehouse:batch', '批次明细', 'resource', parent=wh_mod, sort=3)
    create_meta('sku:warehouse:batch_flow', '批次流水', 'resource', parent=wh_mod, sort=4)

    # L2: 统计
    stat_mod = create_meta('sku:stat_mod', '统计', 'module', parent=sku_cat, sort=30)
    # L3
    create_meta('sku:stat:purchase', '采购报表-产品/明细', 'resource', parent=stat_mod, sort=1)
    create_meta('sku:stat:stock_report', '库存报表-自建-明细', 'resource', parent=stat_mod, sort=2)


    # L1: 单据数据权限
    doc_cat = create_meta(
        'doc', '单据数据权限', 'category',
        desc='控制各类业务单据的可见性，如销售订单、采购单等。'
    )
    # L2: 销售
    sales_mod = create_meta('doc:sales_mod', '销售', 'module', parent=doc_cat, sort=10)
    create_meta('doc:sales:order', '销售订单', 'resource', parent=sales_mod, sort=1)

    db.session.commit()
    click.echo('Data Permission Metas seeded!')

    # --- FIELD PERMISSION SEED ---
    from app.models.field_permission import FieldPermissionMeta
    click.echo('Seeding Field Permission Metas...')

    field_metas = [
        ('product:cost_price', '采购成本', '商品中心', '产品的进货成本'),
        ('product:stock_price', '库存单价', '商品中心', '库存平均单价'),
        ('product:supplier', '供应商', '商品中心', '默认供应商信息'),
        ('order:total_amount', '订单总额', '订单中心', '销售订单的总金额'),
        ('order:customer_phone', '客户电话', '订单中心', '客户联系方式'),
        ('logistics:fee', '物流费用', '物流中心', '实际发生的物流运费'),
        ('finance:profit', '毛利润', '财务中心', '订单毛利'),
    ]

    for key, label, module, desc in field_metas:
        meta = db.session.scalar(select(FieldPermissionMeta).where(FieldPermissionMeta.field_key == key))
        if not meta:
            meta = FieldPermissionMeta(field_key=key, label=label, module=module, description=desc)
            db.session.add(meta)
        else:
            meta.label = label
            meta.module = module
            meta.description = desc
            
    db.session.commit()
    click.echo('Field Permission Metas seeded!')
