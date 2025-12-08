import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.product import ProductVehicle
from sqlalchemy import select

app = create_app()

with app.app_context():
    count = db.session.scalar(select(db.func.count(ProductVehicle.id)))
    print(f"ProductVehicle count: {count}")
    
    roots = db.session.scalars(select(ProductVehicle).where(ProductVehicle.parent_id.is_(None))).all()
    for root in roots:
        print(f"Root: {root.name} ({len(root.children)} children)")

