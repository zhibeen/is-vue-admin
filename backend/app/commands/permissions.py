import click
from flask.cli import AppGroup
from app.extensions import db
from app.models.user import Permission, Role

permissions_cli = AppGroup('permissions', help='权限管理命令')

@click.command('seed-permissions')
@click.option('--clear', is_flag=True, help='清除现有权限数据')
def seed_permissions_cmd(clear):
    """初始化系统权限数据"""
    
    if clear:
        click.echo("正在清除现有权限数据...")
        db.session.query(Permission).delete()
        db.session.commit()
        click.echo("✅ 已清除权限数据")
    
    # 定义所有权限
    permissions_data = [
        # 系统管理模块
        {
            'name': 'system:view',
            'module': '系统管理',
            'resource': '系统概览',
            'action': 'view',
            'description': '查看系统'
        },
        {
            'name': 'system:role:view',
            'module': '系统管理',
            'resource': '角色管理',
            'action': 'view',
            'description': '查看角色'
        },
        {
            'name': 'system:role:manage',
            'module': '系统管理',
            'resource': '角色管理',
            'action': 'manage',
            'description': '管理角色'
        },
        {
            'name': 'system:user:view',
            'module': '系统管理',
            'resource': '用户管理',
            'action': 'view',
            'description': '查看用户'
        },
        {
            'name': 'system:user:manage',
            'module': '系统管理',
            'resource': '用户管理',
            'action': 'manage',
            'description': '管理用户'
        },
        
        # 商品中心模块
        {
            'name': 'product:view',
            'module': '商品中心',
            'resource': '商品列表',
            'action': 'view',
            'description': '查看商品'
        },
        {
            'name': 'product:create',
            'module': '商品中心',
            'resource': '商品列表',
            'action': 'create',
            'description': '创建商品'
        },
        {
            'name': 'product:update',
            'module': '商品中心',
            'resource': '商品列表',
            'action': 'update',
            'description': '编辑商品'
        },
        {
            'name': 'product:delete',
            'module': '商品中心',
            'resource': '商品列表',
            'action': 'delete',
            'description': '删除商品'
        },
        {
            'name': 'vehicle:manage',
            'module': '商品中心',
            'resource': '车型管理',
            'action': 'manage',
            'description': '管理车型'
        },
        
        # 关务模块 (新增)
        {
            'name': 'customs:view',
            'module': '关务管理',
            'resource': '报关单管理',
            'action': 'view',
            'description': '查看报关单'
        },
        {
            'name': 'customs:create',
            'module': '关务管理',
            'resource': '报关单管理',
            'action': 'create',
            'description': '创建报关单'
        },
        {
            'name': 'customs:edit',
            'module': '关务管理',
            'resource': '报关单管理',
            'action': 'update',
            'description': '编辑报关单'
        },
        {
            'name': 'customs:delete',
            'module': '关务管理',
            'resource': '报关单管理',
            'action': 'delete',
            'description': '删除报关单'
        },
        {
            'name': 'customs:approve',
            'module': '关务管理',
            'resource': '报关单管理',
            'action': 'approve',
            'description': '审批报关单'
        },
        {
            'name': 'customs:export',
            'module': '关务管理',
            'resource': '报关单管理',
            'action': 'export',
            'description': '导出报关单'
        },
        {
            'name': 'customs:product:view',
            'module': '关务管理',
            'resource': '归类商品库',
            'action': 'view',
            'description': '查看报关品类'
        },
        {
            'name': 'customs:product:manage',
            'module': '关务管理',
            'resource': '归类商品库',
            'action': 'manage',
            'description': '管理报关品类'
        },
        {
            'name': 'customs:consignee:view',
            'module': '关务管理',
            'resource': '境外收货人',
            'action': 'view',
            'description': '查看收货人'
        },
        {
            'name': 'customs:consignee:manage',
            'module': '关务管理',
            'resource': '境外收货人',
            'action': 'manage',
            'description': '管理收货人'
        },
    ]
    
    created_count = 0
    for perm_data in permissions_data:
        existing = db.session.query(Permission).filter_by(name=perm_data['name']).first()
        if not existing:
            perm = Permission(**perm_data)
            db.session.add(perm)
            created_count += 1
            click.echo(f"创建权限: {perm_data['name']} - {perm_data['description']}")
        else:
            click.echo(f"权限已存在: {perm_data['name']}")
    
    db.session.commit()
    click.echo(f"\n✅ 权限初始化完成！新增 {created_count} 个权限")
    
    # 自动将所有权限分配给 admin 角色
    admin_role = db.session.query(Role).filter_by(name='admin').first()
    if admin_role:
        click.echo("\n正在为 admin 角色分配权限...")
        all_permissions = db.session.query(Permission).all()
        admin_role.permissions = all_permissions
        db.session.commit()
        click.echo(f"✅ 已将 {len(all_permissions)} 个权限分配给 admin 角色")
    else:
        click.secho("⚠️  警告: 未找到 admin 角色，请先运行 flask seed-users", fg='yellow')

permissions_cli.add_command(seed_permissions_cmd)

