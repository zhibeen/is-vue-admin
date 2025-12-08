from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

def reset_tables():
    with app.app_context():
        # Tables to drop in dependency order
        tables = [
            'product_reference_codes',
            'product_variants',
            'product_fitments',
            'products'
        ]
        
        print("Dropping tables...")
        for table in tables:
            try:
                db.session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        
        db.session.commit()
        print("Done.")

if __name__ == "__main__":
    reset_tables()

