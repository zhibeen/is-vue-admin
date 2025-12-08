from flask import Flask

def register_commands(app: Flask):
    """自动注册所有命令"""
    
    # 1. 导入各个模块的命令对象
    from .user import user_cli, seed_users_cmd
    from .system import system_cli
    from .product import product_cli
    from .supply import supply_cli
    from .core import init_dev_cmd, forge_mock_cmd
    from .rebuild import rebuild_cmd
    
    # 2. 注册 Command Groups (带前缀)
    # flask user seed-users
    # flask system seed-system-dicts
    # flask product seed-products
    # flask supply seed-suppliers
    app.cli.add_command(user_cli)
    app.cli.add_command(system_cli)
    app.cli.add_command(product_cli)
    app.cli.add_command(supply_cli)
    
    # 3. 注册 Top-Level Commands (无前缀，为了方便使用)
    # flask init-dev
    # flask forge-mock
    # 同时也保留原来的 seed-* 命令作为顶级命令（为了兼容性，如果团队已经习惯了）
    app.cli.add_command(init_dev_cmd)
    app.cli.add_command(forge_mock_cmd)
    app.cli.add_command(rebuild_cmd)
    
    # 可选：如果你希望旧的 seed-* 命令也能直接在顶级访问 (兼容旧脚本)
    app.cli.add_command(seed_users_cmd)
    
    # 从各 Group 中提取子命令注册到顶级 (可选，视团队习惯而定)
    # 这里我们只把最常用的放出来
