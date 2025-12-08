import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check if table exists in DB
    result = db.session.execute(text("SELECT to_regclass('product_vehicle_brands')")).scalar()
    print(f"product_vehicle_brands exists: {result is not None}")
    
    result = db.session.execute(text("SELECT to_regclass('product_vehicles')")).scalar()
    print(f"product_vehicles exists: {result is not None}")

