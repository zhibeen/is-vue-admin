print("Start script...")
from app import create_app
print("Imported app...")
from app.extensions import db
from app.models.product import ProductVehicle

print("Creating app...")
app = create_app()
print("App created...")

with app.app_context():
    print("Querying...")
    count = db.session.query(ProductVehicle).count()
    print(f"------------")
    print(f"ProductVehicle Count: {count}")
    print(f"------------")
