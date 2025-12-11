import os
import sys
from app import create_app
from app.extensions import db
from app.models.warehouse import Warehouse
from sqlalchemy import select

def check_warehouses():
    env = os.getenv('FLASK_ENV', 'development')
    print(f"Initializing app with FLASK_ENV={env}")
    app = create_app(env)
    with app.app_context():
        print("="*50)
        print("Warehouse Data Inspection")
        print("="*50)
        
        # 1. Total Count
        try:
            stmt_count = select(db.func.count()).select_from(Warehouse)
            count = db.session.scalar(stmt_count)
            print(f"Total Warehouses in DB: {count}")
        except Exception as e:
            print(f"Error querying database: {e}")
            return
        
        if count == 0:
            print("No warehouses found. The database table is empty.")
            return

        # 2. Category Distribution
        try:
            stmt_cats = select(Warehouse.category, db.func.count(Warehouse.id)).group_by(Warehouse.category)
            cat_counts = db.session.execute(stmt_cats).all()
            print("\nCategory Distribution:")
            for cat, cnt in cat_counts:
                print(f"  - '{cat}': {cnt}")
        except Exception as e:
            print(f"Error checking categories: {e}")
            
        # 3. List first 10 items
        print("\nFirst 10 Warehouses:")
        stmt_items = select(Warehouse).limit(10)
        items = db.session.execute(stmt_items).scalars().all()
        for w in items:
            print(f"  ID: {w.id} | Code: {w.code} | Name: {w.name} | Category: '{w.category}' | Status: '{w.status}'")
            
        print("="*50)

if __name__ == '__main__':
    check_warehouses()
