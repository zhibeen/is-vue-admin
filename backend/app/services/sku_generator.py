import re
from sqlalchemy import select
from app.extensions import db
from app.models.product import Product

def generate_sku(category_code: str, make_code: str, suffix: str = None) -> str:
    """
    Generates a new SKU based on the strategy: {Category}{Make}{Serial}{Suffix}
    Example: 188 + 01 + 0051 + L -> 188010051L
    """
    if not category_code:
        category_code = "000" # Fallback
    if not make_code:
        make_code = "00" # Fallback / Universal

    prefix = f"{category_code}{make_code}"
    
    # 1. Find the max existing serial for this prefix
    # We look for SKUs starting with prefix, followed by 4 digits
    # Regex: ^18801\d{4}
    query = select(Product.sku).where(
        Product.sku.regexp_match(f"^{prefix}\\d{{4}}")
    ).order_by(Product.sku.desc()).limit(1)
    
    result = db.session.execute(query).scalar_one_or_none()
    
    next_serial = 1
    if result:
        # Extract the 4 digits after prefix
        # sku: 188010051L -> serial_part: 0051
        try:
            serial_part = result[len(prefix):len(prefix)+4]
            if serial_part.isdigit():
                next_serial = int(serial_part) + 1
        except:
            pass # Fallback to 1 if parsing fails
            
    # 2. Generate Candidate & Check Collision
    while True:
        serial_str = f"{next_serial:04d}"
        candidate_sku = f"{prefix}{serial_str}"
        if suffix:
            candidate_sku += suffix
            
        # Check if exists
        exists = db.session.execute(
            select(Product.id).where(Product.sku == candidate_sku)
        ).scalar_one_or_none()
        
        if not exists:
            return candidate_sku
        
        next_serial += 1

