import sys
import os

# Add the backend directory to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.product import ProductVehicle

app = create_app()

def seed_vehicles():
    with app.app_context():
        print("Seeding ProductVehicle data...")
        
        # Check if data exists
        if db.session.scalars(db.select(ProductVehicle)).first():
            print("Data already exists. Skipping.")
            return

        # 2. Define Data
        # Structure: (Name, Abbreviation, Code, Type, Children)
        data = [
            {
                "name": "Chevrolet", "abbr": "CHE", "code": "1", "type": "brand",
                "children": [
                    {
                        "name": "Silverado", "abbr": "SIL", "code": None, "type": "model",
                        "children": [
                            {"name": "2007-2013", "abbr": "07-13", "code": None, "type": "year"},
                            {"name": "2014-2018", "abbr": "14-18", "code": None, "type": "year"},
                        ]
                    },
                    {
                        "name": "Colorado", "abbr": "COL", "code": None, "type": "model",
                        "children": [
                            {"name": "2015-2022", "abbr": "15-22", "code": None, "type": "year"},
                        ]
                    }
                ]
            },
            {
                "name": "Toyota", "abbr": "TOY", "code": "2", "type": "brand",
                "children": [
                    {
                        "name": "Camry", "abbr": "CAM", "code": None, "type": "model",
                        "children": [
                            {"name": "2018-2023", "abbr": "18-23", "code": None, "type": "year"},
                        ]
                    },
                    {
                        "name": "Corolla", "abbr": "COR", "code": None, "type": "model",
                        "children": []
                    }
                ]
            },
            {
                "name": "Ford", "abbr": "FOR", "code": "3", "type": "brand",
                "children": [
                    {
                        "name": "F-150", "abbr": "F15", "code": None, "type": "model",
                        "children": [
                            {"name": "2015-2020", "abbr": "15-20", "code": None, "type": "year"},
                            {"name": "2021-2023", "abbr": "21-23", "code": None, "type": "year"},
                        ]
                    }
                ]
            }
        ]

        # 3. Insert Data
        for brand_data in data:
            brand = ProductVehicle(
                name=brand_data["name"],
                abbreviation=brand_data["abbr"],
                code=brand_data["code"],
                level_type=brand_data["type"]
            )
            db.session.add(brand)
            db.session.flush() # Get ID

            for model_data in brand_data["children"]:
                model = ProductVehicle(
                    name=model_data["name"],
                    abbreviation=model_data["abbr"],
                    code=model_data["code"],
                    level_type=model_data["type"],
                    parent_id=brand.id
                )
                db.session.add(model)
                db.session.flush()

                for year_data in model_data["children"]:
                    year = ProductVehicle(
                        name=year_data["name"],
                        abbreviation=year_data["abbr"],
                        code=year_data["code"],
                        level_type=year_data["type"],
                        parent_id=model.id
                    )
                    db.session.add(year)
            
        db.session.commit()
        print("Seeding completed successfully.")

if __name__ == "__main__":
    seed_vehicles()
