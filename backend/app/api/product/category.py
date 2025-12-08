from apiflask import APIBlueprint, abort
from sqlalchemy import select
from app.extensions import db
from app.models.product import Category, AttributeDefinition, CategoryAttribute
from app.schemas.product.category import CategoryTreeSchema, CategoryDetailSchema, AttributeDefinitionSchema, CategoryBaseSchema, CategoryAttributeMappingSchema, EffectiveAttributeSchema
from app.security import auth
from app.decorators import permission_required
from app.errors import BusinessError
from app import codes
from apiflask.fields import Boolean

# url_prefix is now /categories (relative to api_v1)
category_bp = APIBlueprint('category', __name__, url_prefix='/categories', tag='Categories')

@category_bp.get('/tree')
@category_bp.auth_required(auth)
@category_bp.doc(summary='获取分类树', description='获取完整的商品分类树结构（包含子分类）。')
@category_bp.output(CategoryTreeSchema(many=True))
def get_category_tree():
    """Get full category tree structure"""
    # Optimized: Fetch all and build tree in memory or use CTE if needed.
    # For simplicity, we fetch roots and let Marshmallow recurse (N+1 risk, but ok for small trees)
    roots = db.session.scalars(
        select(Category)
        .where(Category.parent_id.is_(None))
        .order_by(Category.sort_order)
    ).all()
    # BaseResponse wrapper applied automatically
    return {'data': roots}

@category_bp.post('')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='创建分类', description='创建一个新分类。')
@category_bp.input(CategoryBaseSchema, arg_name='data') # Fix: Explicit arg_name
@category_bp.output(CategoryDetailSchema)
def create_category(data):
    """Create a new category"""
    # Check code uniqueness
    if db.session.scalars(select(Category).where(Category.code == data['code'])).first():
        abort(400, 'Category code already exists')
        
    # Check abbreviation uniqueness
    if data.get('abbreviation'):
        if db.session.scalars(select(Category).where(Category.abbreviation == data['abbreviation'])).first():
            abort(400, 'Abbreviation already exists')

    cat = Category(**data)
    
    # Calculate level based on parent
    if cat.parent_id:
        parent = db.session.get(Category, cat.parent_id)
        if parent:
            cat.level = (parent.level or 0) + 1
        else:
             # Fallback if parent not found (shouldn't happen due to FK but safe to have)
             cat.level = 1 
    else:
        cat.level = 1

    db.session.add(cat)
    db.session.commit()
    
    return {'data': cat}

@category_bp.put('/<int:category_id>')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='更新分类', description='更新现有分类信息。')
@category_bp.input(CategoryBaseSchema, arg_name='data')
@category_bp.output(CategoryDetailSchema)
def update_category(category_id, data):
    """Update an existing category"""
    cat = db.session.get(Category, category_id)
    if not cat:
        raise BusinessError('Category not found', code=codes.NOT_FOUND, status_code=404)

    # Check code uniqueness if changed
    if data.get('code') and data['code'] != cat.code:
        if db.session.scalars(select(Category).where(Category.code == data['code'])).first():
            raise BusinessError('Category code already exists', code=codes.PRODUCT_CATEGORY_DUPLICATE)

    # Check abbreviation uniqueness if changed
    if data.get('abbreviation') and data['abbreviation'] != cat.abbreviation:
        if db.session.scalars(select(Category).where(Category.abbreviation == data['abbreviation'])).first():
            raise BusinessError('Abbreviation already exists', code=codes.PRODUCT_CATEGORY_DUPLICATE)

    # Check is_leaf change: True -> False (Leaf -> Folder)
    if 'is_leaf' in data and cat.is_leaf and not data['is_leaf']:
        # Check if there are products associated
        # Using len(cat.products) assuming lazy='select' or 'dynamic'
        # If cat.products is not loaded, we can query Product table
        from app.models.product import Product
        product_count = db.session.scalar(
            select(db.func.count(Product.id)).where(Product.category_id == cat.id)
        )
        
        if product_count > 0:
            raise BusinessError(
                f'This category has {product_count} products. Cannot convert to folder directly.',
                code=codes.PRODUCT_CATEGORY_MIGRATION_REQUIRED,
                status_code=200, # OK with business code 30010
                data={
                    'require_migration': True,
                    'product_count': product_count,
                    'suggested_child_name': f"{cat.name} (其他)"
                }
            )

    # Update level if parent changed
    if 'parent_id' in data and data['parent_id'] != cat.parent_id:
        if data['parent_id']:
             new_parent = db.session.get(Category, data['parent_id'])
             if new_parent:
                 cat.level = (new_parent.level or 0) + 1
        else:
             cat.level = 1
             
    # TODO: If level changed, need to update all children levels recursively. 
    # For now, assuming deep structure changes are rare.

    for key, value in data.items():
        setattr(cat, key, value)
    
    db.session.commit()
    return {'data': cat}

@category_bp.post('/<int:category_id>/migrate')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='迁移并更新分类', description='将当前分类下的商品迁移到新子分类，并将当前分类转为目录。')
@category_bp.output(CategoryDetailSchema)
def migrate_and_update_category(category_id):
    """Migrate products to a child category and convert parent to folder"""
    cat = db.session.get(Category, category_id)
    if not cat:
        raise BusinessError('Category not found', code=codes.NOT_FOUND, status_code=404)
        
    if not cat.is_leaf:
        # Already a folder, nothing to do
        return {'data': cat}
        
    # Check if products exist
    from app.models.product import Product
    product_count = db.session.scalar(
        select(db.func.count(Product.id)).where(Product.category_id == cat.id)
    )
    
    if product_count == 0:
         cat.is_leaf = False
         db.session.commit()
         return {'data': cat}

    # 1. Create new child category "Others"
    child_name = f"{cat.name} (其他)"
    child_code = f"{cat.code}99" # Simple strategy: append 99
    
    # Ensure code uniqueness (simple retry or check)
    if db.session.scalars(select(Category).where(Category.code == child_code)).first():
        import random
        child_code = f"{cat.code}{random.randint(10,99)}"

    child = Category(
        name=child_name,
        name_en=f"{cat.name_en} (Others)" if cat.name_en else None,
        code=child_code,
        abbreviation=cat.abbreviation, # Inherit abbreviation? Or keep empty? Usually child keeps relevant code.
        parent_id=cat.id,
        is_leaf=True, # The child holds the products
        is_active=cat.is_active,
        description=f"Migrated from parent {cat.name}",
        level=(cat.level or 0) + 1 # Set level
    )
    db.session.add(child)
    db.session.flush() # Get child.id
    
    # 2. Move products
    db.session.query(Product).filter(Product.category_id == cat.id).update({Product.category_id: child.id})
    
    # 3. Update parent
    cat.is_leaf = False
    
    db.session.commit()
    
    return {'data': cat}

@category_bp.delete('/<int:category_id>')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='删除分类', description='删除分类。如果分类下有子分类或关联产品，将无法删除。')
def delete_category(category_id):
    """Delete a category"""
    cat = db.session.get(Category, category_id)
    if not cat:
        abort(404, 'Category not found')
        
    # Check for children
    if db.session.scalars(select(Category).where(Category.parent_id == category_id)).first():
         abort(400, 'Cannot delete category with children')
         
    # Check for products (using relationship or query)
    # Assuming relationship is set up or checking manually
    if cat.products:
        abort(400, 'Cannot delete category with associated products')

    db.session.delete(cat)
    db.session.commit()
    return None

@category_bp.get('/<int:category_id>/attributes')
@category_bp.auth_required(auth)
@category_bp.doc(
    summary='获取分类属性', 
    description='获取指定分类的所有可用属性定义（包括从父分类继承的属性）。'
)
@category_bp.input({'inheritance': Boolean(load_default=False)}, location='query', arg_name='query_data')
@category_bp.output(EffectiveAttributeSchema(many=True))
def get_category_attributes(category_id, query_data):
    """Get all available attributes for a category (including inherited)"""
    cat = db.session.get(Category, category_id)
    if not cat:
        abort(404, 'Category not found')
        
    inheritance = query_data.get('inheritance', False)
    
    # Use CTE for efficient recursive query if inheritance is requested
    if inheritance:
        # Recursive CTE to get category path from root to current
        cte = select(
            Category.id, 
            Category.parent_id, 
            Category.name,
            Category.level
        ).where(Category.id == category_id).cte(name="category_path", recursive=True)

        parent = select(
            Category.id, 
            Category.parent_id, 
            Category.name,
            Category.level
        ).join(cte, Category.id == cte.c.parent_id)

        cte = cte.union_all(parent)

        # Query attributes for all categories in the path
        # Ordered by level (root first) to ensure correct override order
        # But we need to process root -> leaf order for override logic:
        # Root (Level 1) -> ... -> Current (Level N)
        # However, CTE recursive usually goes bottom-up if starting from child.
        # Let's just fetch all IDs in path and re-query or sort in python.
        
        path_query = db.session.execute(select(cte.c.id, cte.c.name).order_by(cte.c.level)).all()
        # The recursive query above walks UP the tree.
        # So we get [Current, Parent, Grandparent...] if we started with current and joined parent_id.
        # Wait, the recursive part: `Category.id == cte.c.parent_id` finds the parent of the previous row.
        # Yes, this walks UP.
        
        # We need to apply attributes from Root -> Current.
        # So we reverse the path obtained from CTE (which is usually Current -> Root or unordered depending on DB)
        # Actually CTE recursive order isn't guaranteed without explicit ordering column, but logically it finds parents.
        
        # Let's simplify: Just get all ancestor IDs + current ID.
        # Then fetch attributes for these IDs and sort by category level/depth? 
        # Category table has 'level' column, but it might not be trusted if not maintained perfectly.
        # But we can trust the path logic.
        
        # Let's do a clean implementation:
        # 1. Get all ancestor categories + current
        ancestors = db.session.scalars(
            select(Category).where(Category.id.in_([row.id for row in path_query]))
        ).all()
        
        # Sort by level (Root -> Leaf)
        # Assuming level is correct. If not, we can rely on parent_id chain.
        # For robustness, let's sort in Python by building the chain.
        
        cat_map = {c.id: c for c in ancestors}
        sorted_chain = []
        curr = cat
        while curr:
            sorted_chain.insert(0, curr)
            if curr.parent_id:
                curr = cat_map.get(curr.parent_id) # Avoid DB hit if already fetched
                if not curr and curr.parent_id: # Fallback if map missing (shouldn't happen)
                     curr = db.session.get(Category, curr.parent_id)
            else:
                curr = None
                
        # Now process attributes from Root to Current
        result_attributes = []
        seen_keys = set()
        
        for c in sorted_chain:
            is_self = (c.id == category_id)
            
            mappings = db.session.scalars(
                select(CategoryAttribute)
                .options(db.joinedload(CategoryAttribute.attribute_definition))
                .where(CategoryAttribute.category_id == c.id)
                .order_by(CategoryAttribute.display_order)
            ).all()
            
            for m in mappings:
                attr_def = m.attribute_definition
                # If key seen, it means parent defined it. 
                # If current category re-defines it (same key), we update/override.
                # BUT our current logic (seen_keys) SKIPS if already seen.
                # This is "Inherit only if not present".
                # Override logic requires: If seen, UPDATE existing entry in result_attributes.
                
                # Let's find if we have it
                existing_index = next((i for i, item in enumerate(result_attributes) if item['key_name'] == attr_def.key_name), -1)
                
                attr_data = {
                    'id': attr_def.id,
                    'key_name': attr_def.key_name,
                    'label': attr_def.label,
                    'data_type': attr_def.data_type,
                    'options': attr_def.options, # Global options
                    'group_name': m.group_name or attr_def.group_name, # Effective group
                    'attribute_scope': m.attribute_scope, # NEW
                    'is_global': attr_def.is_global,
                    'code_weight': attr_def.code_weight,
                    
                    # Link specific
                    'is_required': m.is_required,
                    'display_order': m.display_order,
                    'include_in_code': m.include_in_code,
                    'override_options': m.options, # Raw override
                    'effective_options': m.options if m.options is not None else attr_def.options, # Override logic
                    
                    # Meta
                    'origin': 'self' if is_self else 'inherited',
                    'origin_category_id': c.id,
                    'origin_category_name': c.name,
                    'editable': is_self
                }
                
                if existing_index >= 0:
                    # Override existing
                    result_attributes[existing_index] = attr_data
                else:
                    # Add new
                    result_attributes.append(attr_data)
                    
        return {'data': result_attributes}

    else:
        # Non-inheritance (Old logic for single category)
        result_attributes = []
        process_category_single(cat, result_attributes, is_self=True)
        return {'data': result_attributes}

def process_category_single(c, result_list, is_self=True):
    mappings = db.session.scalars(
        select(CategoryAttribute)
        .options(db.joinedload(CategoryAttribute.attribute_definition))
        .where(CategoryAttribute.category_id == c.id)
        .order_by(CategoryAttribute.display_order)
    ).all()
    
    for m in mappings:
        attr_def = m.attribute_definition
        attr_data = {
            'id': attr_def.id,
            'key_name': attr_def.key_name,
            'label': attr_def.label,
            'data_type': attr_def.data_type,
            'options': attr_def.options, 
            'group_name': m.group_name or attr_def.group_name,
            'attribute_scope': m.attribute_scope, # NEW
            'is_global': attr_def.is_global,
            'code_weight': attr_def.code_weight,
            'is_required': m.is_required,
            'display_order': m.display_order,
            'include_in_code': m.include_in_code,
            'override_options': m.options, 
            'effective_options': m.options if m.options is not None else attr_def.options, 
            'origin': 'self' if is_self else 'inherited',
            'origin_category_id': c.id,
            'origin_category_name': c.name,
            'editable': is_self
        }
        result_list.append(attr_data)

@category_bp.get('/attributes/mappings')
@category_bp.auth_required(auth)
@category_bp.doc(
    summary='获取所有分类属性映射',
    description='获取所有分类与其属性的关联关系。用于前端缓存并根据分类切换动态筛选属性。'
)
@category_bp.output(CategoryAttributeMappingSchema(many=True))
def get_all_category_attributes_mappings():
    """Get all category-attribute mappings"""
    mappings = db.session.scalars(
        select(CategoryAttribute)
        .options(db.joinedload(CategoryAttribute.attribute_definition))
        .order_by(CategoryAttribute.category_id, CategoryAttribute.display_order)
    ).all()
    return {'data': mappings}

# --- Attribute Management ---

@category_bp.get('/attributes/definitions')
@category_bp.auth_required(auth)
@category_bp.doc(summary='获取所有属性定义字典', description='获取系统中定义的所有属性（用于下拉选择）。')
@category_bp.output(AttributeDefinitionSchema(many=True))
def get_attribute_definitions():
    return {'data': db.session.scalars(select(AttributeDefinition).order_by(AttributeDefinition.id)).all()}

@category_bp.post('/attributes/definitions')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='创建属性定义', description='创建新的全局属性定义。')
@category_bp.input(AttributeDefinitionSchema(exclude=['id']), arg_name='data')
@category_bp.output(AttributeDefinitionSchema)
def create_attribute_definition(data):
    # Map schema field 'key' to model field 'key_name'
    if 'key' in data:
        data['key_name'] = data.pop('key')

    # Check key uniqueness
    if db.session.scalars(select(AttributeDefinition).where(AttributeDefinition.key_name == data['key_name'])).first():
        abort(400, 'Attribute key already exists')
        
    attr = AttributeDefinition(**data)
    db.session.add(attr)
    db.session.commit()
    return {'data': attr}

@category_bp.put('/attributes/definitions/<int:attr_id>')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='更新属性定义', description='更新全局属性定义。')
@category_bp.input(AttributeDefinitionSchema(partial=True), arg_name='data')
@category_bp.output(AttributeDefinitionSchema)
def update_attribute_definition(attr_id, data):
    attr = db.session.get(AttributeDefinition, attr_id)
    if not attr:
        abort(404, 'Attribute not found')
        
    # Map schema field 'key' to model field 'key_name'
    if 'key' in data:
        data['key_name'] = data.pop('key')

    if 'key_name' in data and data['key_name'] != attr.key_name:
        if db.session.scalars(select(AttributeDefinition).where(AttributeDefinition.key_name == data['key_name'])).first():
            abort(400, 'Attribute key already exists')
            
    for key, value in data.items():
        if hasattr(attr, key):
            setattr(attr, key, value)
        
    db.session.commit()
    return {'data': attr}

@category_bp.delete('/attributes/definitions/<int:attr_id>')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='删除属性定义', description='删除全局属性定义。如果已被使用，可能无法删除。')
def delete_attribute_definition(attr_id):
    attr = db.session.get(AttributeDefinition, attr_id)
    if not attr:
        abort(404, 'Attribute not found')
        
    # Check usage
    usage = db.session.scalar(select(db.func.count(CategoryAttribute.category_id)).where(CategoryAttribute.attribute_id == attr.id))
    if usage > 0:
        abort(400, f'Attribute is used in {usage} categories')
        
    db.session.delete(attr)
    db.session.commit()
    return None

@category_bp.post('/<int:category_id>/attributes')
@category_bp.auth_required(auth)
@category_bp.doc(summary='关联属性到分类', description='将现有属性定义关联到指定分类。')
@category_bp.input(CategoryAttributeMappingSchema(only=['attribute_id', 'is_required', 'display_order', 'include_in_code', 'options', 'group_name', 'attribute_scope']), arg_name='data')
@category_bp.output(CategoryAttributeMappingSchema)
def add_category_attribute(category_id, data):
    cat = db.session.get(Category, category_id)
    if not cat:
        abort(404, 'Category not found')
        
    attr_id = data['attribute_id']
    
    # Check if already exists
    exists = db.session.scalar(
        select(CategoryAttribute)
        .where(CategoryAttribute.category_id == category_id, CategoryAttribute.attribute_id == attr_id)
    )
    if exists:
        abort(400, 'Attribute already associated with this category')
    
    mapping = CategoryAttribute(
        category_id=category_id,
        attribute_id=attr_id,
        is_required=data.get('is_required', False),
        display_order=data.get('display_order', 0),
        include_in_code=data.get('include_in_code', None),
        options=data.get('options', None),
        group_name=data.get('group_name', None),
        attribute_scope=data.get('attribute_scope', 'spu')
    )
    db.session.add(mapping)
    db.session.commit()
    
    return {'data': mapping}

@category_bp.put('/<int:category_id>/attributes/<int:attribute_id>')
@category_bp.auth_required(auth)
@category_bp.doc(summary='更新分类属性关联', description='更新关联配置（如排序、必填）。')
@category_bp.input(CategoryAttributeMappingSchema(partial=True), arg_name='data')
@category_bp.output(CategoryAttributeMappingSchema)
def update_category_attribute(category_id, attribute_id, data):
    mapping = db.session.scalar(
        select(CategoryAttribute)
        .where(CategoryAttribute.category_id == category_id, CategoryAttribute.attribute_id == attribute_id)
    )
    if not mapping:
        abort(404, 'Association not found')
        
    for key, value in data.items():
        if hasattr(mapping, key):
            setattr(mapping, key, value)
            
    db.session.commit()
    return {'data': mapping}

@category_bp.delete('/<int:category_id>/attributes/<int:attribute_id>')
@category_bp.auth_required(auth)
@category_bp.doc(summary='移除分类属性关联', description='移除该分类下的指定属性关联。')
def remove_category_attribute(category_id, attribute_id):
    mapping = db.session.scalar(
        select(CategoryAttribute)
        .where(CategoryAttribute.category_id == category_id, CategoryAttribute.attribute_id == attribute_id)
    )
    if not mapping:
        abort(404, 'Association not found')
        
    db.session.delete(mapping)
    db.session.commit()
    return None

@category_bp.post('/<int:category_id>/attributes/copy_from/<int:source_category_id>')
@category_bp.auth_required(auth)
@permission_required('category:manage')
@category_bp.doc(summary='复制属性配置', description='从其他分类复制属性配置到当前分类（仅复制自定义属性，覆盖现有配置）。')
@category_bp.output(EffectiveAttributeSchema(many=True))
def copy_category_attributes(category_id, source_category_id):
    """Copy attribute configuration from another category"""
    target_cat = db.session.get(Category, category_id)
    source_cat = db.session.get(Category, source_category_id)
    
    if not target_cat or not source_cat:
        abort(404, 'Category not found')
        
    if target_cat.id == source_cat.id:
        abort(400, 'Cannot copy from self')

    # Get source attributes (only self-defined ones to avoid duplication of inherited)
    source_mappings = db.session.scalars(
        select(CategoryAttribute)
        .where(CategoryAttribute.category_id == source_category_id)
    ).all()
    
    if not source_mappings:
        return {'data': []} # Nothing to copy

    # Clear existing target mappings (Optional: strategy could be merge, but overwrite is cleaner)
    # For now, let's keep existing and only add/update based on source
    # Or strict copy: delete all current self-definitions and apply source's
    
    # Strategy: Merge/Overwrite. 
    # If target has attr A, update it. If not, create it.
    
    cloned_count = 0
    for src_map in source_mappings:
        # Check if target already has this attribute defined
        target_map = db.session.scalar(
            select(CategoryAttribute)
            .where(
                CategoryAttribute.category_id == category_id, 
                CategoryAttribute.attribute_id == src_map.attribute_id
            )
        )
        
        if target_map:
            # Update existing
            target_map.is_required = src_map.is_required
            target_map.display_order = src_map.display_order
            target_map.include_in_code = src_map.include_in_code
            target_map.options = src_map.options # Copy JSONB value
            target_map.group_name = src_map.group_name
            target_map.attribute_scope = src_map.attribute_scope
        else:
            # Create new
            new_map = CategoryAttribute(
                category_id=category_id,
                attribute_id=src_map.attribute_id,
                is_required=src_map.is_required,
                display_order=src_map.display_order,
                include_in_code=src_map.include_in_code,
                options=src_map.options,
                group_name=src_map.group_name,
                attribute_scope=src_map.attribute_scope
            )
            db.session.add(new_map)
        
        cloned_count += 1
            
    db.session.commit()
    
    # Return updated attributes list (reuse get logic)
    # We can just return empty and let frontend reload, or return the list
    # To keep consistent with get_category_attributes response format:
    # It's better to let frontend reload by calling get attributes API.
    # But APIFlask expects output matching schema. 
    # Let's call the logic from get_category_attributes (refactor needed for clean call)
    # or just return a simple success message if we change output schema.
    # For now, let's just return the processed attributes manually constructed or empty list triggers reload.
    
    return {'data': []} # Frontend should reload
