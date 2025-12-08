import os
import shutil
import subprocess
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models.user import User, Role

app = create_app()

def run_cmd(cmd):
    print(f"Running: {cmd}")
    subprocess.check_call(cmd, shell=True)

def rebuild():
    with app.app_context():
        # 1. Drop Schema
        print("Dropping public schema...")
        with db.engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            conn.commit()
        
        # 2. Delete migrations
        migrations_dir = os.path.join(os.getcwd(), 'migrations', 'versions')
        if os.path.exists(migrations_dir):
            print(f"Cleaning migrations dir: {migrations_dir}")
            for f in os.listdir(migrations_dir):
                if f.endswith('.py'):
                    os.remove(os.path.join(migrations_dir, f))
            print("Deleted migration files.")
        
        # 3. Migrate & Upgrade
        # We need to run this as a shell command
        try:
            run_cmd("flask db migrate -m 'reset_init'")
            run_cmd("flask db upgrade")
        except Exception as e:
            print(f"Migration failed: {e}")
            return
        
        # 3.1 Seed Product Brands (Required for SPU generation)
        print("Seeding Product Brands...")
        try:
            from app.models.product import ProductVehicleBrand
            brands_data = [
                {'name': '大众', 'code': '01'},
                {'name': '宝马', 'code': '02'},
                {'name': '奔驰', 'code': '03'},
                {'name': '福特', 'code': '04'},
                {'name': '标致', 'code': '05'},
                {'name': '欧宝', 'code': '06'},
                {'name': '雷诺', 'code': '07'},
                {'name': '菲亚特', 'code': '08'},
                {'name': '沃尔沃', 'code': '09'},
                {'name': '马自达', 'code': '10'},
                {'name': '尼桑', 'code': '11'},
                {'name': '丰田', 'code': '12'},
                {'name': '铃木', 'code': '13'},
                {'name': '现代', 'code': '14'},
                {'name': '本田', 'code': '15'},
                {'name': '三菱', 'code': '16'},
                {'name': '大宇', 'code': '17'},
                {'name': '吉普', 'code': '18'},
                {'name': '起亚', 'code': '19'},
                {'name': '依维柯', 'code': '20'},
                {'name': '萨博', 'code': '21'},
                {'name': '通用', 'code': '22'},
                {'name': '路虎', 'code': '23'},
                {'name': '雪佛兰', 'code': '24'},
                {'name': '道奇', 'code': '25'},
                {'name': 'GMC', 'code': '26'},
                {'name': '克莱斯勒', 'code': '27'},
                {'name': '其他', 'code': '99'},
            ]
            for b in brands_data:
                if not ProductVehicleBrand.query.filter_by(code=b['code']).first():
                    db.session.add(ProductVehicleBrand(**b))
            db.session.commit()
            print("✅ Product Brands Seeded.")
        except Exception as e:
            print(f"Error seeding brands: {e}")

        # Seed System Dicts
        print("Seeding System Dicts...")
        try:
            from app.models.system import SysDict
            
            # 1. Create Dict
            dict_obj = SysDict.query.filter_by(code='product_business_type').first()
            if not dict_obj:
                items_data = [
                    {'value': 'vehicle', 'label': '汽配产品 (Vehicle)', 'meta_data': {'strategy': 'vehicle'}, 'sort': 10},
                    {'value': 'general', 'label': '通用产品 (General)', 'meta_data': {'strategy': 'general'}, 'sort': 20},
                    {'value': 'electronics', 'label': '电子产品 (Electronics)', 'meta_data': {'strategy': 'general'}, 'sort': 30},
                ]
                # Convert to value_options format
                value_options = [{'value': item['value'], 'label': item['label'], 'meta_data': item.get('meta_data')} for item in items_data]
                
                dict_obj = SysDict(
                    code='product_business_type', 
                    name='产品业务类型', 
                    is_system=True,
                    value_options=value_options
                )
                db.session.add(dict_obj)
                db.session.commit()
            print("✅ System Dicts Seeded.")
        except Exception as e:
            print(f"Error seeding dicts: {e}")

        # 4. Seed Admin
        print("Seeding Admin...")
        try:
            if not User.query.filter_by(username='admin').first():
                admin_role = Role.query.filter_by(name='admin').first()
                if not admin_role:
                    admin_role = Role(name='admin', description='Administrator')
                    db.session.add(admin_role)
                
                admin = User(username='admin', email='admin@example.com', nickname='Admin')
                admin.set_password('password')
                admin.roles.append(admin_role)
                db.session.add(admin)
                db.session.commit()
                print("Created admin user: admin / password")
        except Exception as e:
            print(f"Error creating admin: {e}")

        # 5. Run Seeds
        print("Running Seeds...")
        try:
            run_cmd("flask seed-companies")
            run_cmd("flask seed-categories")
            run_cmd("flask seed-products")
            run_cmd("flask seed-suppliers")
        except Exception as e:
             print(f"Seeding failed: {e}")
        
        print("✅ Rebuild Complete!")

if __name__ == '__main__':
    rebuild()

