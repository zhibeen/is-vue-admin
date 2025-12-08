import click
from flask.cli import AppGroup
from app.extensions import db
from werkzeug.security import generate_password_hash

# 创建一个 AppGroup，但如果不希望有前缀，也可以直接用 @click.command() 然后在 __init__ 里注册
# 为了保持原有的 `flask seed-users` 格式，我们这里直接定义命令对象
# 但通常更好的做法是使用 Blueprint 或者 AppGroup.
# 这里为了保持扁平命令结构（如 flask seed-users 而不是 flask user seed），我们使用 click.command() 并单独暴露

user_cli = AppGroup('user', help='用户管理命令')

@click.command('seed-users')
@click.option('--clear', is_flag=True, help='清除现有用户数据')
def seed_users_cmd(clear):
    """生成初始用户和角色数据 (Admin)"""
    from app.models.user import User, Role, UserRole
    
    if clear:
        click.echo("正在清除用户和角色数据...")
        # 先删除关联表数据
        db.session.query(UserRole).delete()
        # 再删除主表
        db.session.query(User).delete()
        db.session.query(Role).delete()
        db.session.commit()
        click.echo("✅ 已清除用户数据")

    # 1. Create Roles
    roles_data = [
        {'name': 'admin', 'description': '超级管理员'},
        {'name': 'user', 'description': '普通用户'}
    ]
    
    role_map = {}
    for r_data in roles_data:
        role = db.session.query(Role).filter_by(name=r_data['name']).first()
        if not role:
            role = Role(name=r_data['name'], description=r_data['description'])
            db.session.add(role)
            click.echo(f"创建角色: {r_data['name']}")
        role_map[r_data['name']] = role
    
    db.session.flush()
    
    # 2. Create Users
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'password',
            'role': 'admin'
        },
        {
            'username': 'user',
            'email': 'user@example.com',
            'password': 'password',
            'role': 'user'
        }
    ]
    
    for u_data in users_data:
        user = db.session.query(User).filter_by(username=u_data['username']).first()
        if not user:
            user = User(
                username=u_data['username'],
                email=u_data['email'],
                password_hash=generate_password_hash(u_data['password']),
                is_active=True
            )
            # Assign role
            role = role_map.get(u_data['role'])
            if role and role not in user.roles:
                user.roles.append(role)
            
            db.session.add(user)
            click.echo(f"创建用户: {u_data['username']} / {u_data['password']}")
    
    db.session.commit()
    click.echo("✅ 用户初始化完成！")

# 这里为了兼容 Flask 的命令注册方式
# 如果我们在 __init__.py 中使用 app.cli.add_command(seed_users_cmd)，它就会注册为 flask seed-users
user_cli = seed_users_cmd

