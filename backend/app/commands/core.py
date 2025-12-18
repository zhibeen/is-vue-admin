import click
import os
from flask.cli import AppGroup
from app.extensions import db

# 导入具体命令函数，以便在聚合命令中 invoke
from .user import seed_users_cmd
from .permissions import seed_permissions_cmd
from .system import seed_system_dicts_cmd, seed_companies_cmd
from .product import seed_categories_cmd, seed_vehicles_cmd, seed_products_cmd
from .supply import seed_suppliers_cmd, seed_contracts_cmd

# 定义核心命令组
core_cli = AppGroup('core', help='核心聚合命令')

@click.command('init-dev')
@click.option('--reset', is_flag=True, help='警告：这将删除所有数据并重建数据库')
@click.pass_context
def init_dev_cmd(ctx, reset):
    """【环境初始化】一键设置开发环境 (结构+基础数据)"""
    
    click.secho('🚀 开始初始化开发环境...', fg='green', bold=True)
    
    # 1. 数据库重置 (仅在开发环境且指定--reset时)
    if reset:
        if os.getenv('FLASK_ENV') == 'production':
            click.secho('❌ 生产环境禁止使用 --reset!', fg='red')
            return
        
        click.secho('⚠️  正在重置数据库...', fg='yellow')
        db.drop_all()
        db.create_all()
        click.echo('✅ 数据库表结构已重建')

    # 2. 执行基础数据填充 (按依赖顺序)
    try:
        # 2.1 用户与角色 (最基础)
        click.secho('\n📦 [1/6] 初始化用户与角色...', fg='cyan')
        ctx.invoke(seed_users_cmd, clear=reset)
        
        # 2.2 系统权限 (依赖角色)
        click.secho('\n📦 [2/6] 初始化系统权限...', fg='cyan')
        ctx.invoke(seed_permissions_cmd, clear=reset)
        
        # 2.3 系统字典 (被其他模块引用)
        click.secho('\n📦 [3/6] 初始化系统字典与配置...', fg='cyan')
        ctx.invoke(seed_system_dicts_cmd, clear=reset)
        
        # 2.4 内部公司主体
        click.secho('\n📦 [4/6] 初始化内部公司主体...', fg='cyan')
        ctx.invoke(seed_companies_cmd, clear=reset)
        
        # 2.5 产品分类树 (产品基础)
        click.secho('\n📦 [5/6] 初始化产品分类与属性...', fg='cyan')
        ctx.invoke(seed_categories_cmd, clear=reset)

        # 2.6 车型数据 (虽然量大，但是属于参考数据，非业务数据)
        click.secho('\n📦 [6/6] 初始化车型标准库...', fg='cyan')
        ctx.invoke(seed_vehicles_cmd, clear=reset)
        
        click.secho('\n✨ 开发环境初始化完成！你现在可以启动应用了。', fg='green', bold=True)
        
    except Exception as e:
        click.secho(f'\n❌ 初始化过程中发生错误: {e}', fg='red')
        db.session.rollback()
        raise e

@click.command('forge-mock')
@click.option('--volume', default='small', type=click.Choice(['small', 'medium', 'large']), help='数据量级')
@click.pass_context
def forge_mock_cmd(ctx, volume):
    """【数据模拟】生成测试用的业务流水数据"""
    
    # 定义不同量级的配置
    config = {
        'small': {'supplier': 10, 'product': 20, 'contract': 5},
        'medium': {'supplier': 50, 'product': 200, 'contract': 50},
        'large': {'supplier': 200, 'product': 1000, 'contract': 200}
    }
    
    cfg = config[volume]
    
    click.secho(f'🛠️  开始生成模拟数据 (模式: {volume})...', fg='green', bold=True)
    
    try:
        # 1. 供应商
        click.secho(f'\n🔨 [1/3] 生成虚拟供应商 ({cfg["supplier"]}个)...', fg='cyan')
        ctx.invoke(seed_suppliers_cmd, count=cfg['supplier'], clear=False)
        
        # 2. 产品 (SPU/SKU)
        click.secho(f'\n🔨 [2/3] 生成虚拟产品 ({cfg["product"]}个)...', fg='cyan')
        ctx.invoke(seed_products_cmd, count=cfg['product'], clear=False)
        
        # 3. 采购合同
        click.secho(f'\n🔨 [3/3] 生成虚拟采购合同 ({cfg["contract"]}份)...', fg='cyan')
        ctx.invoke(seed_contracts_cmd, count=cfg['contract'], clear=False)
        
        click.secho(f'\n✨ 模拟数据生成完成！', fg='green')
        
    except Exception as e:
        click.secho(f'\n❌ 生成过程中发生错误: {e}', fg='red')

# 注册到 Group (其实这两个命令更适合直接挂载到 app.cli，但为了模块统一，我们可以先挂到 core，或者在 __init__ 中特殊处理)
# 为了让用户直接使用 flask init-dev (不带前缀)，我们在 __init__.py 中会将它们单独提取出来注册
# 或者我们可以直接把这两个函数暴露出去

