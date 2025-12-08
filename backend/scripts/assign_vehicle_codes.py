import sys
import os
import csv
from sqlalchemy import select

# Add the backend directory to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.product import ProductVehicle

app = create_app()

def assign_codes():
    with app.app_context():
        print("Starting Vehicle Code Assignment...")
        
        # 1. Load Reference Data
        csv_path = os.path.join(os.path.dirname(__file__), 'vehicle_reference_data.csv')
        make_map = {} # Name -> Code
        model_map = {} # MakeName -> { ModelName -> Code }
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    m_name = row['make_en'].strip()
                    m_code = row['make_code'].strip()
                    md_name = row['model_en'].strip()
                    md_code = row['model_code'].strip()
                    
                    make_map[m_name.lower()] = m_code
                    
                    if m_name.lower() not in model_map:
                        model_map[m_name.lower()] = {}
                    
                    if md_name:
                        model_map[m_name.lower()][md_name.lower()] = md_code
        except FileNotFoundError:
            print(f"Error: {csv_path} not found.")
            return

        print(f"Loaded {len(make_map)} makes and {sum(len(v) for v in model_map.values())} models from CSV.")

        # 2. Fix Level Types (brand -> make)
        # Ensure consistency with sys_dict
        brands_to_fix = db.session.scalars(select(ProductVehicle).where(ProductVehicle.level_type == 'brand')).all()
        for b in brands_to_fix:
            b.level_type = 'make'
        if brands_to_fix:
            print(f"Fixed {len(brands_to_fix)} nodes from 'brand' to 'make'.")

        # 3. Update Makes
        makes = db.session.scalars(
            select(ProductVehicle).where(ProductVehicle.level_type == 'make')
        ).all()
        
        for make in makes:
            key = make.name.lower()
            if key in make_map:
                make.code = make_map[key]
                print(f"Updated Make {make.name}: {make.code}")
            else:
                # Fallback to 99 if not in list
                if not make.code:
                    make.code = '99'
                    print(f"Assigned Make {make.name}: 99 (Not in CSV)")
        
        db.session.flush()
        
        # 4. Update Models
        # Process make by make to handle sequence
        for make in makes:
            models = db.session.scalars(
                select(ProductVehicle)
                .where(ProductVehicle.parent_id == make.id)
                .where(ProductVehicle.level_type == 'model')
                .order_by(ProductVehicle.name)
            ).all()
            
            make_key = make.name.lower()
            ref_models = model_map.get(make_key, {})
            
            # Track used codes to assign sequential ones
            used_codes = set()
            # First pass: Assign from CSV
            for model in models:
                model_key = model.name.lower()
                if model_key in ref_models:
                    model.code = ref_models[model_key]
                    used_codes.add(int(model.code))
            
            # Second pass: Assign sequential for missing
            next_code = 1
            for model in models:
                if not model.code:
                    # Find next available
                    while next_code in used_codes:
                        next_code += 1
                    
                    if next_code > 99:
                        model.code = '99' # Cap at 99
                    else:
                        model.code = f"{next_code:02d}"
                        used_codes.add(next_code)
                    
                    print(f"Assigned Model {make.name} -> {model.name}: {model.code}")

        db.session.commit()
        print("Vehicle Code Assignment Completed.")

if __name__ == "__main__":
    assign_codes()

