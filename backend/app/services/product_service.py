from typing import List, Dict, Any
from sqlalchemy import select, or_, and_
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

    def list_skus(self, page: int = 1, per_page: int = 20, filters: Dict[str, Any] = None):
        """
        获取SKU列表，支持多维度筛选
        
        Args:
            page: 页码
            per_page: 每页数量
            filters: 筛选条件字典，包含：
                - q: 搜索关键词 (SKU编码、特征码、产品名称)
                - category_id: 分类ID
                - brand: 品牌
                - model: 车型
                - attribute_filters: 属性筛选 {key: value}
                - stock_min: 最小库存
                - stock_max: 最大库存
                - is_active: 是否启用
        """
        # 基础查询：关联Product和Category
        stmt = select(ProductVariant).join(
            Product, ProductVariant.product_id == Product.id
        ).join(
            Category, Product.category_id == Category.id
        ).options(
            selectinload(ProductVariant.product).selectinload(Product.category)
        )
        
        # 应用筛选条件
        if filters:
            # 搜索关键词
            if filters.get('q'):
                q = f"%{filters['q']}%"
                stmt = stmt.where(
                    or_(
                        ProductVariant.sku.ilike(q),
                        ProductVariant.feature_code.ilike(q),
                        Product.name.ilike(q),
                        Product.spu_code.ilike(q)
                    )
                )
            
            # 分类筛选
            if filters.get('category_id'):
                stmt = stmt.where(Product.category_id == filters['category_id'])
            
            # 品牌/车型筛选
            if filters.get('brand'):
                stmt = stmt.where(Product.brand == filters['brand'])
            if filters.get('model'):
                stmt = stmt.where(Product.spu_coding_metadata['model'].astext == filters['model'])
            
            # 状态筛选
            if 'is_active' in filters:
                stmt = stmt.where(ProductVariant.is_active == filters['is_active'])
            
            # 属性筛选 (JSONB字段查询)
            if filters.get('attribute_filters'):
                for key, value in filters['attribute_filters'].items():
                    # 查询 specs JSONB字段中的属性
                    stmt = stmt.where(
                        ProductVariant.specs[key].astext == str(value)
                    )
        
        # 排序：默认按创建时间倒序
        stmt = stmt.order_by(ProductVariant.created_at.desc())
        
        # 分页查询
        pagination = db.paginate(stmt, page=page, per_page=per_page)
        
        # 转换结果格式
        items = []
        for variant in pagination.items:
            product = variant.product
            category = product.category
            
            # 构建属性显示字符串
            attributes_display = []
            if variant.specs:
                for key, value in variant.specs.items():
                    if value:
                        attributes_display.append(f"{key}:{value}")
            
            item = {
                'sku': variant.sku,
                'feature_code': variant.feature_code or '',
                'product_id': product.id,
                'product_name': product.name,
                'spu_code': product.spu_code,
                'category_id': category.id,
                'category_name': category.name,
                'brand': product.brand,
                'model': product.spu_coding_metadata.get('model') if product.spu_coding_metadata else None,
                'attributes_display': ', '.join(attributes_display) if attributes_display else '-',
                'stock_quantity': 0,  # TODO: 集成库存系统后填充
                'safety_stock': 0,    # TODO: 集成库存系统后填充
                'in_transit': 0,      # TODO: 集成库存系统后填充
                'warning_status': 'normal',  # TODO: 根据库存计算
                'quality_type': variant.quality_type,
                'is_active': variant.is_active,
                'created_at': variant.created_at.isoformat() if variant.created_at else None,
                'updated_at': variant.updated_at.isoformat() if variant.updated_at else None,
            }
            items.append(item)
        
        return {
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    def get_sku_detail(self, sku: str) -> Dict[str, Any]:
        """
        获取SKU详情
        
        Args:
            sku: SKU编码
        """
        # 查询SKU及其关联数据
        stmt = select(ProductVariant).where(ProductVariant.sku == sku).options(
            selectinload(ProductVariant.product).selectinload(Product.category),
            selectinload(ProductVariant.product).selectinload(Product.reference_codes),
            selectinload(ProductVariant.product).selectinload(Product.fitments)
        )
        
        variant = db.session.scalars(stmt).first()
        if not variant:
            raise BusinessError(f'SKU {sku} not found', 404)
        
        product = variant.product
        category = product.category
        
        # 解析编码规则
        coding_rules = self._parse_sku_coding_rules(variant.sku, category)
        
        # 构建属性显示
        attributes = variant.specs or {}
        
        # 构建合规信息
        compliance_info = {
            'hs_code': variant.hs_code.code if variant.hs_code else None,
            'declared_name': variant.declared_name,
            'declared_unit': variant.declared_unit,
            'net_weight': float(variant.net_weight) if variant.net_weight else None,
            'gross_weight': float(variant.gross_weight) if variant.gross_weight else None,
            'package_dimensions': f"{variant.pack_length or 0}×{variant.pack_width or 0}×{variant.pack_height or 0}cm" 
                                  if variant.pack_length and variant.pack_width and variant.pack_height else None,
        }
        
        # 构建参考编码列表
        reference_codes = []
        for rc in product.reference_codes:
            reference_codes.append({
                'code': rc.code,
                'code_type': rc.code_type,
                'brand': rc.brand
            })
        
        # 构建适配车型列表
        fitments = []
        for fitment in product.fitments:
            fitments.append({
                'make': fitment.make,
                'model': fitment.model,
                'sub_model': fitment.sub_model,
                'year_start': fitment.year_start,
                'year_end': fitment.year_end,
                'position': fitment.position
            })
        
        # 构建属性显示字符串
        attributes_display = []
        for key, value in attributes.items():
            if value:
                attributes_display.append(f"{key}:{value}")
        
        result = {
            'sku': variant.sku,
            'feature_code': variant.feature_code or '',
            'product_id': product.id,
            'product_name': product.name,
            'spu_code': product.spu_code,
            'category_id': category.id,
            'category_name': category.name,
            'brand': product.brand,
            'model': product.spu_coding_metadata.get('model') if product.spu_coding_metadata else None,
            'attributes': attributes,
            'attributes_display': ', '.join(attributes_display) if attributes_display else '-',
            'compliance_info': compliance_info,
            'coding_rules': coding_rules,
            'reference_codes': reference_codes,
            'fitments': fitments,
            'stock_quantity': 0,  # TODO: 集成库存系统后填充
            'safety_stock': 0,    # TODO: 集成库存系统后填充
            'in_transit': 0,      # TODO: 集成库存系统后填充
            'warning_status': 'normal',  # TODO: 根据库存计算
            'quality_type': variant.quality_type,
            'is_active': variant.is_active,
            'created_at': variant.created_at.isoformat() if variant.created_at else None,
            'updated_at': variant.updated_at.isoformat() if variant.updated_at else None,
        }
        
        return result

    def _parse_sku_coding_rules(self, sku: str, category: Category) -> Dict[str, Any]:
        """
        解析SKU编码规则
        
        根据双轨制编码规则解析SKU的各个部分：
        - 类目码(3位)
        - 车型码(4位): Brand(2位) + Model(2位)
        - 流水号(2位)
        - 属性后缀(可选)
        """
        if len(sku) < 9:
            return {}
        
        try:
            # 解析各个部分
            category_code = sku[:3]  # 前3位：类目码
            vehicle_code = sku[3:7]  # 第4-7位：车型码
            serial = sku[7:9]        # 第8-9位：流水号
            suffix = sku[9:] if len(sku) > 9 else ''  # 剩余部分：属性后缀
            
            # 解析车型码
            brand_code = vehicle_code[:2] if len(vehicle_code) >= 2 else ''
            model_code = vehicle_code[2:4] if len(vehicle_code) >= 4 else ''
            
            return {
                'category_code': category_code,
                'vehicle_code': vehicle_code,
                'brand_code': brand_code,
                'model_code': model_code,
                'serial': serial,
                'suffix': suffix,
                'category_abbreviation': category.abbreviation or '',
                'category_code_db': category.code or ''
            }
        except Exception as e:
            logger.warning(f"Failed to parse SKU coding rules for {sku}: {e}")
            return {}

    def update_sku(self, sku: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新SKU信息
        
        注意：只能更新非编码相关的字段（价格、库存、状态等）
        """
        variant = db.session.scalar(select(ProductVariant).where(ProductVariant.sku == sku))
        if not variant:
            raise BusinessError(f'SKU {sku} not found', 404)
        
        # 允许更新的字段
        updatable_fields = [
            'price', 'cost_price', 'net_weight', 'gross_weight',
            'pack_length', 'pack_width', 'pack_height',
            'hs_code_id', 'declared_name', 'declared_unit',
            'quality_type', 'is_active', 'barcode', 'image'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(variant, field, data[field])
        
        # 更新specs（变体属性）
        if 'specs' in data:
            variant.specs = data['specs']
        
        db.session.commit()
        
        return self.get_sku_detail(sku)

    def delete_sku(self, sku: str) -> None:
        """
        删除SKU
        
        注意：删除前需要检查是否有库存或订单关联
        """
        variant = db.session.scalar(select(ProductVariant).where(ProductVariant.sku == sku))
        if not variant:
            raise BusinessError(f'SKU {sku} not found', 404)
        
        # TODO: 检查库存和订单关联
        # if variant.has_inventory or variant.has_orders:
        #     raise BusinessError('Cannot delete SKU with inventory or orders', 400)
        
        db.session.delete(variant)
        db.session.commit()

    def toggle_sku_status(self, sku: str) -> Dict[str, Any]:
        """
        切换SKU状态（启用/停用）
        """
        variant = db.session.scalar(select(ProductVariant).where(ProductVariant.sku == sku))
        if not variant:
            raise BusinessError(f'SKU {sku} not found', 404)
        
        variant.is_active = not variant.is_active
        db.session.commit()
        
        return {
            'sku': variant.sku,
            'is_active': variant.is_active,
            'message': f'SKU状态已切换为{"启用" if variant.is_active else "停用"}'
        }
