import re
from sqlalchemy import select
from app.extensions import db
from app.models.product import Product, ProductVariant

def get_next_serial_preview(prefix: str) -> str:
    """
    Returns the next 4-digit serial string (e.g. '0052') for the given prefix
    by looking at the max existing SKU in the DB.
    """
    if not prefix:
        return '0001'

    # Regex: ^prefix\d{4}
    # We want to find SKUs that start with this prefix and have digits immediately after.
    # Note: DB lookup might be slow if table is huge without index on SKU (which we have).
    query = select(ProductVariant.sku).where(
        ProductVariant.sku.regexp_match(f"^{prefix}\\d{{4}}")
    ).order_by(ProductVariant.sku.desc()).limit(1)
    
    result = db.session.execute(query).scalar_one_or_none()
    
    next_serial = 1
    if result:
        try:
            # Extract the 4 digits after prefix
            serial_part = result[len(prefix):len(prefix)+4]
            if serial_part.isdigit():
                next_serial = int(serial_part) + 1
        except:
            pass 
            
    return f"{next_serial:04d}"

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
    
    # 1. Get initial guess based on max serial
    next_serial_str = get_next_serial_preview(prefix)
    next_serial = int(next_serial_str)
    
    # 2. Generate Candidate & Check Collision
    while True:
        serial_str = f"{next_serial:04d}"
        candidate_sku = f"{prefix}{serial_str}"
        if suffix:
            candidate_sku += suffix
            
        # Check if exists
        exists = db.session.execute(
            select(ProductVariant.id).where(ProductVariant.sku == candidate_sku)
        ).scalar_one_or_none()
        
        if not exists:
            return candidate_sku
        
        next_serial += 1
