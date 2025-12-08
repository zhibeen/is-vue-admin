import click
from flask.cli import with_appcontext
from app.extensions import db

@click.command('rebuild')
@click.pass_context
@with_appcontext
def rebuild_cmd(ctx):
    """一键重置数据库并注入所有初始数据"""
    from app.commands.system import seed_system_dicts_cmd, seed_companies_cmd
    from app.commands.product import seed_categories_cmd, seed_vehicles_cmd
    from app.commands.user import seed_users_cmd
    
    # 1. 确认操作
    if not click.confirm('警告：此操作将清空所有数据并重置数据库！确定要继续吗？'):
        click.echo('操作已取消')
        return

    # 2. 清空并重建数据库结构
    click.echo("\n[1/6] 重置数据库结构...")
    db.drop_all()
    db.create_all()
    
    # 标记 Alembic 版本为最新
    from flask_migrate import stamp
    stamp()
    
    click.echo("✅ 数据库结构已重置")

    # 3. 注入初始用户
    click.echo("\n[2/6] 注入初始用户...")
    ctx.invoke(seed_users_cmd, clear=False)

    # 4. 注入系统字典
    click.echo("\n[3/6] 注入系统字典...")
    ctx.invoke(seed_system_dicts_cmd, clear=False)
    
    # 5. 注入公司主体
    click.echo("\n[4/6] 注入公司主体...")
    ctx.invoke(seed_companies_cmd, clear=False)
    
    # 6. 注入产品分类及属性
    click.echo("\n[5/6] 注入产品分类及属性...")
    ctx.invoke(seed_categories_cmd, clear=False)
    
    # 7. 注入车辆数据
    click.echo("\n[6/6] 注入基础车辆数据...")
    ctx.invoke(seed_vehicles_cmd, clear=False)

    click.echo("\n✨✨✨ 系统重构完成！✨✨✨")
