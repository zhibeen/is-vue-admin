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

def seed_vehicles():
    with app.app_context():
        print("Seeding full vehicle data from CSV...")
        
        # 1. Clear existing data? 
        # For safety in development, we might want to clear or update.
        # Let's clear for now to ensure clean state matching CSV.
        # Be careful in production!
        if os.environ.get('FLASK_ENV') == 'development':
            print("Clearing existing vehicle data...")
            db.session.query(ProductVehicle).delete()
            db.session.commit()
        
        # 2. Load CSV
        csv_path = os.path.join(os.path.dirname(__file__), 'vehicle_reference_data.csv')
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Cache nodes to avoid DB lookups
                makes = {} 
                models = {}
                platforms = {}
                
                rows = list(reader)
                print(f"Processing {len(rows)} rows...")

                for row in rows:
                    make_code = row['make_code'].strip()
                    make_name = row['make_en'].strip()
                    model_code = row['model_code'].strip()
                    model_name = row['model_en'].strip()
                    platform_code = row.get('platform_code', '').strip()
                    platform_name = row.get('platform_en', '').strip()
                    year_range = row.get('year', '').strip()
                    
                    if not make_code or not make_name:
                        continue

                    # 1. Process Make
                    if make_code not in makes:
                        make = ProductVehicle(
                            name=make_name,
                            abbreviation=make_name[:3].upper(), # Simple abbr generation
                            code=make_code,
                            level_type='make'
                        )
                        db.session.add(make)
                        db.session.flush() # Get ID
                        makes[make_code] = make
                    
                    current_make = makes[make_code]
                    
                    if not model_code or not model_name:
                        continue

                    # 2. Process Model
                    model_key = f"{make_code}-{model_code}"
                    if model_key not in models:
                        model = ProductVehicle(
                            name=model_name,
                            abbreviation=model_name[:3].upper().replace(' ', ''), # Simple abbr
                            code=model_code,
                            level_type='model',
                            parent_id=current_make.id
                        )
                        db.session.add(model)
                        db.session.flush()
                        models[model_key] = model
                    
                    current_model = models[model_key]
                    current_parent_for_years = current_model
                    
                    # 3. Process Platform (Optional)
                    if platform_code and platform_name:
                        platform_key = f"{model_key}-{platform_code}"
                        
                        if platform_key not in platforms:
                            platform = ProductVehicle(
                                name=platform_name,
                                abbreviation=platform_name.upper(),
                                code=platform_code, # Use code from CSV
                                level_type='platform',
                                parent_id=current_model.id
                            )
                            db.session.add(platform)
                            db.session.flush()
                            platforms[platform_key] = platform
                        
                        current_parent_for_years = platforms[platform_key]
                    
                    # 4. Process Years
                    if year_range:
                        try:
                            start_year, end_year = 0, 0
                            if '-' in year_range:
                                parts = year_range.split('-')
                                start_year = int(parts[0])
                                end_part = parts[1].strip()
                                if not end_part or end_part.lower() == 'present':
                                    end_year = 2024
                                else:
                                    end_year = int(end_part)
                            else:
                                start_year = int(year_range)
                                end_year = start_year
                                
                            # Generate year nodes
                            for y in range(start_year, end_year + 1):
                                y_str = str(y)
                                # Simple duplicate check could be added if needed, but flushing every time is slow
                                # Assuming distinct ranges per parent in CSV
                                year_node = ProductVehicle(
                                    name=y_str,
                                    abbreviation=y_str[2:], # '23'
                                    code=y_str[2:], # '23'
                                    level_type='year',
                                    parent_id=current_parent_for_years.id
                                )
                                db.session.add(year_node)
                                
                        except ValueError as ve:
                            print(f"Skipping invalid year range '{year_range}' for {model_name}: {ve}")
                            
                db.session.commit()
                print("Seeding completed successfully.")
                
        except FileNotFoundError:
            print(f"Error: {csv_path} not found.")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    seed_vehicles()
