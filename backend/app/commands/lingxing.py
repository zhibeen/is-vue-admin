"""领星API权限初始化命令"""
import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import Permission


@click.group()
def lingxing():
    """领星API管理命令"""
    pass


@lingxing.command('init-permissions')
@with_appcontext
def init_permissions():
    """初始化领星API相关权限"""
    
    permissions = [
        {
            'code': 'lingxing:shipment:view',
            'name': '查看发货单',
            'description': '允许查询领星发货单详情',
            'resource': 'lingxing',
            'action': 'view'
        },
        {
            'code': 'lingxing:stock:view',
            'name': '查看备货单',
            'description': '允许查询领星备货单详情',
            'resource': 'lingxing',
            'action': 'view'
        },
        {
            'code': 'lingxing:health:check',
            'name': '健康检查',
            'description': '允许执行领星API连接测试',
            'resource': 'lingxing',
            'action': 'check'
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    for perm_data in permissions:
        existing = Permission.query.filter_by(code=perm_data['code']).first()
        
        if existing:
            # 更新现有权限
            existing.name = perm_data['name']
            existing.description = perm_data['description']
            existing.resource = perm_data['resource']
            existing.action = perm_data['action']
            updated_count += 1
            click.echo(f"更新权限: {perm_data['code']}")
        else:
            # 创建新权限
            new_permission = Permission(**perm_data)
            db.session.add(new_permission)
            created_count += 1
            click.echo(f"创建权限: {perm_data['code']}")
    
    db.session.commit()
    
    click.echo(f"\n权限初始化完成!")
    click.echo(f"- 新增: {created_count} 个")
    click.echo(f"- 更新: {updated_count} 个")
    click.echo(f"- 总计: {len(permissions)} 个")
    click.echo("\n提示: 请在后台为相应角色分配这些权限")

