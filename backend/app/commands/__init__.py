from flask import Flask

def register_commands(app: Flask):
    """自动注册所有命令"""
    
    # 1. 导入各个模块的命令对象
    from .user import user_cli, seed_users_cmd
    from .permissions import permissions_cli
    from .system import system_cli
    from .product import product_cli
    from .supply import supply_cli
    from .serc import serc_cli
    from .customs import customs_cli
    from .core import init_dev_cmd, forge_mock_cmd
    from .rebuild import rebuild_cmd
    from .warehouse import warehouse_cli
    from .lingxing import lingxing
    from .shipment import shipment
    from .logistics import logistics
    
    # 2. 注册 Command Groups (带前缀)
    app.cli.add_command(user_cli)
    app.cli.add_command(permissions_cli)
    app.cli.add_command(system_cli)
    app.cli.add_command(product_cli)
    app.cli.add_command(supply_cli)
    app.cli.add_command(serc_cli)
    app.cli.add_command(customs_cli)
    app.cli.add_command(warehouse_cli)
    app.cli.add_command(lingxing)
    app.cli.add_command(shipment)
    app.cli.add_command(logistics)
    
    # 3. 注册 Top-Level Commands (无前缀，为了方便使用)
    # flask init-dev
    # flask forge-mock
    # 同时也保留原来的 seed-* 命令作为顶级命令（为了兼容性，如果团队已经习惯了）
    app.cli.add_command(init_dev_cmd)
    app.cli.add_command(forge_mock_cmd)
    app.cli.add_command(rebuild_cmd)
    # app.cli.add_command(seed_warehouse_command) # 已移至 warehouse group
    
    # 可选：如果你希望旧的 seed-* 命令也能直接在顶级访问 (兼容旧脚本)
    app.cli.add_command(seed_users_cmd)
    
    # 从各 Group 中提取子命令注册到顶级 (可选，视团队习惯而定)
    # 这里我们只把最常用的放出来
