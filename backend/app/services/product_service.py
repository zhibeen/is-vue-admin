from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.product import Product, ProductFitment
from app.models.category import Category
from app.services.sku_generator import generate_sku
from app.errors import BusinessError

class ProductService:
    def create_product(self, data: dict) -> Product:
        # 1. Resolve Category Code for SKU (Inheritance Logic)
        category = db.session.get(Category, data['category_id'])
        if not category:
            raise BusinessError('Category not found', 404)
            
        # Walk up to find a valid code (e.g., 189 -> 188)
        category_code = "000"
        curr = category
        while curr:
            if curr.code:
                category_code = curr.code
                break
            curr = curr.parent
            
        # 2. Generate SKU
        # TODO: Get Make Code from fitments if available, or use '00' (Universal)
        make_code = "00" 
        
        sku = generate_sku(category_code, make_code, data.get('suffix_code'))
        
        # 3. Create Product
        product = Product(
            sku=sku,
            name=data['name'],
            feature_code=data.get('feature_code'),
            category_id=data['category_id'],
            parent_sku_id=data.get('parent_sku_id'),
            suffix_code=data.get('suffix_code'),
            length=data.get('length'),
            width=data.get('width'),
            height=data.get('height'),
            weight=data.get('weight'),
            attributes=data.get('attributes', {})
        )
        
        # 4. Add Fitments
        for fitment_data in data.get('fitments', []):
            fitment = ProductFitment(
                vehicle_id=fitment_data['vehicle_id'],
                notes=fitment_data.get('notes')
            )
            product.fitments.append(fitment)
            
        db.session.add(product)
        db.session.commit()
        
        return product

    def get_product(self, product_id: int) -> Product:
        # Use selectinload to avoid N+1 when accessing fitments/category later
        stmt = select(Product).options(
            selectinload(Product.fitments),
            selectinload(Product.category)
        ).where(Product.id == product_id)
        
        product = db.session.scalars(stmt).first()
        if not product:
            raise BusinessError('Product not found', 404)
        return product

    def list_products(self, page: int = 1, per_page: int = 20, q: str = None, sort: str = 'id'):
        # Use selectinload to avoid N+1 for list view
        stmt = select(Product).options(
            selectinload(Product.category) 
        )
        
        # Filtering
        if q:
            # Search in name or sku
            stmt = stmt.where(
                (Product.name.ilike(f"%{q}%")) | 
                (Product.sku.ilike(f"%{q}%"))
            )
            
        # Sorting
        if sort:
            desc = False
            if sort.startswith('-'):
                sort = sort[1:]
                desc = True
                
            if hasattr(Product, sort):
                col = getattr(Product, sort)
                stmt = stmt.order_by(col.desc() if desc else col.asc())
            else:
                # Default fallback
                stmt = stmt.order_by(Product.id.desc())
        else:
            stmt = stmt.order_by(Product.id.desc())
        
        # Pagination
        pagination = db.paginate(stmt, page=page, per_page=per_page)
        return pagination

