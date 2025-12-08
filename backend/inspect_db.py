from app import create_app
from app.extensions import db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    try:
        columns = inspector.get_columns('products')
        print("--- Columns in 'products' table ---")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")
            
        print("\n--- Columns in 'product_variants' table ---")
        v_columns = inspector.get_columns('product_variants')
        for col in v_columns:
            print(f"- {col['name']} ({col['type']})")
            
    except Exception as e:
        print(f"Error inspecting DB: {e}")

