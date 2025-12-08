from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.product import Product, ProductVariant, ProductReferenceCode, ProductFitment, Category
from app.services.code_builder import CodeBuilderService
from app.errors import BusinessError
import logging

logger = logging.getLogger(__name__)

class ProductService:
    """
    Product Service V2.0
    Integrated with CodeBuilderService for dual-track coding system.
    """

    def create_product(self, data: dict) -> Product:
        """
        创建产品 (SPU + Variants)
        Data format expectation:
        {
            "category_id": 1,
            "name": "Silverado Headlight",
            "brand": "CHE",
            "model": "SIL",
            "year": "07-13",
            "attributes": {...}, 
            "variants": [
                {
                    "sku": "127...", (Optional, for legacy)
                    "suffix": "WB", (Optional, for generating new short code)
                    "specs": {"color": "Chrome", "position": "Left"},
                    ...
                }
            ]
        }
        """
        category_id = data.get('category_id')
        if not category_id:
            raise BusinessError("Category ID is required")
            
        category = db.session.get(Category, category_id)
        if not category:
            raise BusinessError(f"Category {category_id} not found")

        # 1. Check if SPU exists (Upsert Logic)
        # 如果前端没有传 spu_code，则自动生成
        spu_code = data.get('spu_code')
        
        # 优先使用显式的 spu_coding_metadata，否则尝试从 data 根节点提取
        input_metadata = data.get('spu_coding_metadata') or data
        
        if not spu_code:
            try:
                spu_code = CodeBuilderService.generate_spu_code(category_id, input_metadata)
            except ValueError as e:
                raise BusinessError(str(e))
        
        # Check existing SPU
        spu = db.session.scalar(select(Product).filter_by(spu_code=spu_code))
        is_new_spu = False
        
        if not spu:
            # Create New SPU
            is_new_spu = True
            # 准备存入数据库的 coding metadata
            # 如果前端传了结构化的 metadata，直接使用；否则从扁平 data 中提取关键字段
            if data.get('spu_coding_metadata'):
                spu_coding_metadata = data.get('spu_coding_metadata')
            else:
                spu_coding_metadata = {
                    k: v for k, v in data.items() 
                    if k in ['brand', 'model', 'year', 'year_start', 'year_end', 'engine', 'series', 'brand_id']
                }
                
            spu = Product(
                spu_code=spu_code,
                name=data['name'],
                category_id=category_id,
                spu_coding_metadata=spu_coding_metadata, # 存入元数据
                description=data.get('description'),
                main_image=data.get('main_image'),
                attributes=data.get('attributes', {}),
                brand=data.get('brand')
            )
            db.session.add(spu)
            db.session.flush() # Get SPU ID
        else:
            # Update existing SPU (basic fields) if needed?
            # For now, we only trust name updates if explicitly needed, but let's be conservative.
            # We mainly want to attach variants to this SPU.
            pass
        
        # 2. Create Variants (SKUs) - Upsert Logic
        stats = {
            'total': len(data.get('variants', [])),
            'new': 0,
            'updated': 0,
            'existing': 0
        }
        new_variants_skus = []
        existing_variants_skus = []
        
        for v_data in data.get('variants', []):
            specs = v_data.get('specs', {})
            
            # A. 生成 SKU 特征码 (用于展示和核对)
            feature_code = v_data.get('feature_code')
            if not feature_code:
                feature_code = CodeBuilderService.generate_sku_feature_code(spu.spu_code, specs, category_id=category_id)
            
            # B. 生成/确定 SKU 短码 (用于扫码)
            sku = v_data.get('sku')
            suffix_code = v_data.get('suffix_code') # 允许前端显式传后缀
            
            if not sku:
                # New variant generation
                try:
                    sku = CodeBuilderService.generate_sku_short_code(category_id, suffix_code)
                except Exception as e:
                    logger.error(f"Failed to generate SKU short code: {e}")
                    raise BusinessError("Failed to generate SKU short code")

            # Check if variant exists (by SKU)
            existing_variant = db.session.scalar(select(ProductVariant).filter_by(sku=sku))
            
            if existing_variant:
                # Update existing variant? 
                stats['existing'] += 1
                existing_variants_skus.append(sku)
                
                # Update mutable fields (price, cost, weight, etc.)
                existing_variant.price = v_data.get('price') or existing_variant.price
                existing_variant.cost_price = v_data.get('cost_price') or existing_variant.cost_price
                existing_variant.weight = v_data.get('weight') or existing_variant.weight
                existing_variant.specs = specs or existing_variant.specs 
            else:
                # Create new variant
                stats['new'] += 1
                new_variants_skus.append(sku)
                
                variant = ProductVariant(
                    product_id=spu.id,
                    sku=sku,
                    feature_code=feature_code,
                    quality_type=v_data.get('quality_type', 'Aftermarket'),
                    specs=specs,
                    price=v_data.get('price'),
                    cost_price=v_data.get('cost_price'),
                    weight=v_data.get('weight'),
                    hs_code_id=v_data.get('hs_code_id'),
                    declared_name=v_data.get('declared_name'),
                    declared_unit=v_data.get('declared_unit')
                )
                db.session.add(variant)
            
        # 3. Create Reference Codes (Append only)
        for rc_data in data.get('reference_codes', []):
            # Check exist
            exists = db.session.scalar(select(ProductReferenceCode).filter_by(
                product_id=spu.id, 
                code=rc_data['code'], 
                code_type=rc_data['code_type']
            ))
            if not exists:
                rc = ProductReferenceCode(
                    product_id=spu.id,
                    code=rc_data['code'],
                    code_type=rc_data['code_type'],
                    brand=rc_data.get('brand')
                )
                db.session.add(rc)
            
        # 4. Create Fitments (Append only)
        # 简单去重逻辑可能不够，实际业务可能允许相同车型不同年份。
        # 暂不处理 Fitment 深度去重，由前端控制
        if is_new_spu:
            for fit_data in data.get('fitments', []):
                fitment = ProductFitment(
                    product_id=spu.id,
                    make=fit_data.get('make'),
                    model=fit_data.get('model'),
                    sub_model=fit_data.get('sub_model'),
                    year_start=fit_data.get('year_start'),
                    year_end=fit_data.get('year_end'),
                    notes=fit_data.get('notes'),
                    fitment_type=fit_data.get('fitment_type')
                )
                db.session.add(fitment)
            
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if 'duplicate key value violates unique constraint' in str(e) and 'ix_product_variants_sku' in str(e):
                raise BusinessError('Generated SKU collision detected. Please check variant attributes for duplicates.', 409)
            raise e
            
        # Return detailed result
        return {
            'spu_code': spu.spu_code,
            'action': 'created' if is_new_spu else 'merged',
            'stats': stats,
            'new_variants': new_variants_skus,
            'existing_variants': existing_variants_skus
        }

    def get_product(self, product_id: int) -> Product:
        stmt = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.variants),
            selectinload(Product.reference_codes),
            selectinload(Product.fitments)
        ).where(Product.id == product_id)
        
        product = db.session.scalars(stmt).first()
        if not product:
            raise BusinessError('Product not found', 404)
        return product

    def list_products(self, page: int = 1, per_page: int = 20, q: str = None, sort: str = 'id'):
        stmt = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.variants) 
        )
        
        # Filtering
        if q:
            # Search in SPU name, SPU code, Variant SKU, Reference Code, OR JSON Metadata
            # Note: JSON searching syntax depends on DB (PG uses ->>)
            stmt = stmt.outerjoin(ProductVariant).outerjoin(ProductReferenceCode).where(
                (Product.name.ilike(f"%{q}%")) | 
                (Product.spu_code.ilike(f"%{q}%")) |
                (ProductVariant.sku.ilike(f"%{q}%")) |
                (ProductVariant.feature_code.ilike(f"%{q}%")) | # Search by feature code
                (ProductReferenceCode.code.ilike(f"%{q}%"))
            ).distinct()
            
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
                stmt = stmt.order_by(Product.id.desc())
        else:
            stmt = stmt.order_by(Product.id.desc())
        
        pagination = db.paginate(stmt, page=page, per_page=per_page)
        return pagination

    def update_product(self, product_id: int, data: dict) -> Product:
        # 简单实现 update，暂不处理编码重新生成
        # 如果需要支持“修改车型导致编码变更”，逻辑会非常复杂(涉及库存迁移)
        # 专家建议: 关键编码属性一旦生成，原则上不允许修改。如需修改，建议下架重发。
        product = self.get_product(product_id)
        
        if 'name' in data: product.name = data['name']
        if 'description' in data: product.description = data['description']
        if 'attributes' in data: product.attributes = data['attributes']
        
        # Update variants? 
        # Update fitments?
        # 暂略，需根据具体前端交互设计实现
        
        db.session.commit()
        return product
