import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.product import ProductVehicle

app = create_app()

with app.app_context():
    print("Tables in metadata:")
    for t in db.metadata.tables.keys():
        print(f"- {t}")
    
    if "product_vehicles" in db.metadata.tables:
        print("SUCCESS: product_vehicles found in metadata")
    else:
        print("FAILURE: product_vehicles NOT found in metadata")

