import logging
from typing import Dict, Optional, List, Any
from sqlalchemy import select, func
from app.extensions import db
from app.models.product import Category, ProductVariant, ProductVehicle, AttributeDefinition

logger = logging.getLogger(__name__)

class CodeBuilderService:
    """
    V2.0 产品编码生成服务 (Code Builder)
    
    负责实现双轨制编码逻辑:
    1. SPU Feature Code: 模板驱动，支持 {cat}-{brand}-{model}-{year} 或 {cat}-{brand}-{series} 等任意组合
    2. SKU Short Code: 18800521WB
    3. SKU Feature Code: ...-2P-CH-AM-WB
    """

    @staticmethod
    def generate_spu_code(category_id: int, metadata: Dict[str, Any]) -> str:
        """
        生成 SPU 特征码 (全动态模板模式)
        """
        # 1. 获取类目及模板 (支持递归继承)
        category = db.session.get(Category, category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")
            
        # 递归查找 spu_config
        template = None
        curr = category
        while curr:
            spu_config = getattr(curr, "spu_config", None)
            if spu_config and spu_config.get("template"):
                template = spu_config.get("template")
                break
            # 如果没有找到配置，继续向父级查找
            if curr.parent_id:
                # 假设 parent 关系已预加载，如果未加载可能会触发额外查询
                # 这里为了稳健，如果 curr.parent 没加载，我们手动查一下
                if not curr.parent:
                     curr = db.session.get(Category, curr.parent_id)
                else:
                     curr = curr.parent
            else:
                curr = None

        if not template:
            # 默认兜底策略
            if category.business_type == 'general':
                 # 通用件默认: 类目-品牌-系列
                 template = "{cat}-{brand}-{series}"
            else:
                 # 汽配默认: 类目-品牌-车型-年份
                 template = "{cat}-{brand}-{model}-{year}"
        
        # 2. 准备上下文 (Context)
        context = {}
        
        # [系统级变量] - 需要特殊计算的
        # FIX: category.abbreviation can be None, use fallback
        context["cat"] = (category.abbreviation or "UNK").upper()
        context["brand"] = CodeBuilderService._resolve_brand(metadata)
        context["year"] = CodeBuilderService._resolve_year(metadata)
        
        # [动态变量] - 直接注入 Metadata
        # 比如 metadata={"engine": "2.0T", "power": "60W"}
        # 自动注入 context["engine"] = "2.0T"
        for k, v in metadata.items():
            # 跳过已处理的 key，或者是 ID 类 key
            if k in ["brand_id", "brand", "year_start", "year_end", "year"]:
                continue
            
            # 清洗数据: 转字符串，转大写，去空格
            clean_val = str(v).upper().strip() if v is not None else "00"
            context[k] = clean_val
            
        # 3. 渲染模板
        return CodeBuilderService._render_template(template, context)
            
    @staticmethod
    def _render_template(template: str, context: Dict) -> str:
        """
        渲染模板，支持智能空值处理
        例如模板 "{cat}-{brand}-{series}-{voltage}"
        如果 voltage 为空，自动生成 "cat-brand-series"，而不是 "cat-brand-series-"
        """
        import re
        
        # 1. 提取模板中所有需要的 key: {key}
        required_keys = re.findall(r"\{(\w+)\}", template)
        
        safe_context = context.copy()
        for key in required_keys:
            val = safe_context.get(key)
            # 如果 key 不存在，或值为 None/Empty/"00"，则视为"空"
            # 注意: 0 是有意义的数字，不能视为 Empty
            if val is None or val == "" or val == "00":
                safe_context[key] = ""
            else:
                # 确保是字符串
                safe_context[key] = str(val)
        
        # 2. 初步渲染
        # 此时 {voltage} 会被替换为 ""
        # 结果可能变成: "HL-CHE-PRO-" 或 "HL--PRO-"
        try:
            raw_str = template.format(**safe_context)
        except KeyError as e:
            # 理论上上面已经补全了空串，这里不应该报错，除非 format 语法错误
            raise ValueError(f"模板格式错误: {e}")
        
        # 3. 智能清洗 (Smart Cleaning)
        # 替换连续的分隔符 (目前假设分隔符是 -)
        # 更加通用的做法是替换所有非字母数字的连续符号，这里先针对横杠
        clean_str = re.sub(r"-+", "-", raw_str)
        
        # 去除首尾的分隔符
        clean_str = clean_str.strip("-")
        
        # 4. 兜底检查
        if not clean_str:
            raise ValueError("生成失败: 所有编码字段均为空")
            
        return clean_str

    @staticmethod
    def _resolve_brand(metadata: Dict) -> str:
        """解析品牌缩写"""
        # Legacy support: if brand_id is still passed, we try to look it up in ProductVehicle (level_type=brand)
        if "brand_id" in metadata:
            # Try to find in new table
            brand = db.session.get(ProductVehicle, metadata["brand_id"])
            if brand and brand.level_type == 'brand' and brand.abbreviation:
                return brand.abbreviation
        
        if "brand" in metadata:
            # 如果直接传了字符串 (New preferred way)
            return str(metadata["brand"]).upper().strip()
            
        return "GEN" # Generic

    @staticmethod
    def _resolve_year(metadata: Dict) -> str:
        """解析年份段 (2007,2013 -> 07-13)"""
        if "year_start" in metadata and "year_end" in metadata:
            try:
                s = str(metadata["year_start"])[-2:]
                e = str(metadata["year_end"])[-2:]
                return f"{s}-{e}"
            except:
                return "00-00"
        
        if "year" in metadata:
            return str(metadata["year"]).upper().strip()
            
        return "00-00"

    @staticmethod
    def generate_sku_short_code(category_id: int, suffix: str = None) -> str:
        """
        生成 SKU 短码 (物流码)
        策略: CategoryCode(3) + Sequence(5) + Suffix(2)
        """
        category = db.session.get(Category, category_id)
        cat_code = category.code or "999"
        
        prefix = cat_code
        # 查找最大流水号 (建议生产环境换 Redis)
        last_sku = db.session.execute(
            select(ProductVariant.sku)
            .where(ProductVariant.sku.like(f"{prefix}%"))
            .order_by(func.length(ProductVariant.sku).desc(), ProductVariant.sku.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        next_seq = 1
        if last_sku:
            try:
                # 假设格式: 188 00521 ...
                num_part = last_sku[len(prefix):len(prefix)+5]
                if num_part.isdigit():
                    next_seq = int(num_part) + 1
            except:
                pass
                
        seq_str = f"{next_seq:05d}"
        clean_suffix = (suffix or "").upper().strip()[:3]
        
        return f"{prefix}{seq_str}{clean_suffix}"

    @staticmethod
    def preview_product_codes(category_id: int, spu_metadata: Dict[str, Any], variants_specs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        预览 API 专用方法
        批量生成 SPU Code 和 Variants SKU/Feature Code
        关键: 模拟流水号分配 (Grouping Strategy)
        """
        result = {
            'spu_code': '',
            'variants': []
        }
        
        # 1. Generate SPU Code
        try:
            spu_code = CodeBuilderService.generate_spu_code(category_id, spu_metadata)
            result['spu_code'] = spu_code
        except Exception as e:
            spu_code = "SPU-PREVIEW-ERROR"
            result['spu_code'] = spu_code
            
        # 2. Group Variants by Implicit Attributes (Color, etc.)
        # Implicit Attrs: attribute_scope='sku' AND include_in_code=False
        
        # Pre-fetch all definitions needed
        # Collect all keys from all variants
        all_keys = set()
        for specs in variants_specs:
            all_keys.update(specs.keys())
            
        attr_defs = db.session.execute(
            select(AttributeDefinition).where(AttributeDefinition.key_name.in_(list(all_keys)))
        ).scalars().all()
        def_map = {d.key_name: d for d in attr_defs}
        
        # Fetch Category Overrides
        from app.models.product import CategoryAttribute
        cat_attrs = db.session.execute(
            select(CategoryAttribute)
            .where(
                CategoryAttribute.category_id == category_id,
                CategoryAttribute.attribute_id.in_([d.id for d in attr_defs])
            )
        ).scalars().all()
        cat_attr_map = {ca.attribute_id: ca for ca in cat_attrs}
        
        # Helper to determine properties
        def get_attr_props(key):
            defn = def_map.get(key)
            if not defn: return (None, False, False) # (code, is_sku_scope, include_in_code)
            
            # Defaults
            is_sku = True # Assume SKU unless specified SPU
            include = defn.include_in_code if defn.include_in_code is not None else True
            
            # --- Heuristic Defaults if Config Missing (L2.0 Rules) ---
            key_upper = key.upper()
            if "COLOR" in key_upper or "颜色" in key_upper:
                if defn.include_in_code is None: include = False # Default Color to Implicit
            elif "POSITION" in key_upper or "位置" in key_upper:
                if defn.include_in_code is None: include = True # Default Position to Explicit
            # --------------------------------------------
            
            if defn.id in cat_attr_map:
                ca = cat_attr_map[defn.id]
                if ca.attribute_scope == 'spu': is_sku = False
                if ca.include_in_code is not None: include = ca.include_in_code
            
            return (defn, is_sku, include)

        # Grouping
        # Key: tuple of values of implicit attributes
        # Value: List of (index, specs)
        groups = {} 
        
        for idx, specs in enumerate(variants_specs):
            implicit_key_parts = []
            
            # Sort keys to ensure stable grouping key
            sorted_keys = sorted(specs.keys())
            
            for k in sorted_keys:
                defn, is_sku, include = get_attr_props(k)
                if is_sku and not include:
                    # This is an implicit attribute (e.g. Color)
                    # It contributes to the Group Key
                    # Use extracted code for grouping to handle normalization
                    code_val = CodeBuilderService._extract_code_from_options(defn.options, specs[k])
                    implicit_key_parts.append(f"{k}:{code_val}")
            
            group_key = tuple(implicit_key_parts)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append((idx, specs))
            
        # 3. Assign Mock Serials to Groups
        
        category = db.session.get(Category, category_id)
        cat_code = category.code or "999"
        
        make_code = spu_metadata.get('make_code', '00')
        model_code = spu_metadata.get('model_code', '00')
        prefix = f"{cat_code}{make_code}{model_code}" # 3+2+2 = 7 digits
        
        # --- Fix: Reuse existing serial if SPU exists ---
        from app.models.product import Product
        existing_spu = db.session.scalar(select(Product).filter_by(spu_code=result['spu_code']))
        start_serial = 1
        
        if existing_spu:
            # Check if this SPU has any variants
            first_variant = db.session.execute(
                select(ProductVariant)
                .where(ProductVariant.product_id == existing_spu.id)
                .limit(1)
            ).scalar_one_or_none()
            
            if first_variant and first_variant.sku and first_variant.sku.startswith(prefix):
                try:
                    # Extract serial from existing SKU (e.g. 11202020301DRD -> 01)
                    # Length of prefix is 7. Serial is next 2 digits.
                    serial_part = first_variant.sku[len(prefix):len(prefix)+2]
                    if serial_part.isdigit():
                        start_serial = int(serial_part)
                        # Important: In reuse mode, we force ALL variants to use this serial
                        # So we don't increment it.
                        logger.info(f"Reusing serial {start_serial} from existing SPU {existing_spu.spu_code}")
                except:
                    pass
        else:
            # New SPU: Find next available serial globally for this prefix
            last_sku = db.session.execute(
                select(ProductVariant.sku)
                .where(ProductVariant.sku.like(f"{prefix}%"))
                .order_by(func.length(ProductVariant.sku).desc(), ProductVariant.sku.desc())
                .limit(1)
            ).scalar_one_or_none()
            
            if last_sku:
                try:
                    num_part = last_sku[len(prefix):len(prefix)+2] 
                    if num_part.isdigit():
                        start_serial = int(num_part) + 1
                except:
                    pass
                
        # Assign serials to groups
        group_serials = {}
        
        # If reusing (existing_spu is True), we use the SAME serial for all new variants too
        # assuming the grouping logic (implicit attributes) hasn't changed drastically to require split.
        # Currently we support "One SPU, One Serial".
        
        if existing_spu:
             # Force same serial for all groups
             # This means "Color" variants share the serial "01", distinguished by suffix (implied empty suffix for color?)
             # Wait, our rule is:
             # Implicit Attrs (Color) -> Same Serial? No.
             # Implicit Attrs (Color) -> Different Suffix?
             # Let's look at logic below: "implicit_key_parts" are used for GROUPING.
             # If Color is Implicit, then different colors go to DIFFERENT groups?
             # No, if Color is implicit (not in code), it means it DOES NOT change the code?
             # If include_in_code=False, it contributes to Group Key?
             
             # Re-reading logic:
             # if is_sku and not include: implicit_key_parts.append(...)
             # So different colors -> Different Group Keys.
             # Different Group Keys -> Different Serials.
             
             # THIS IS THE PROBLEM with Color!
             # If Color is "Implicit" (not in suffix), then different colors MUST have different Serials to be unique.
             # Example: 112...01 (Red), 112...02 (Blue).
             
             # BUT, if we are reusing SPU, and we add "Green".
             # We should probably get "03"? Or should we reuse "01" and rely on suffix?
             # If Color is Implicit, there is NO suffix for color. So we MUST use "03".
             
             # However, your case "112...01DRD" implies Position is Explicit (Suffix D/P), Color is Explicit (Suffix RD/BK).
             # Check your metadata: "include_in_code" for Color is likely TRUE?
             # If Color is Explicit (Suffix RD), then "implicit_key_parts" is EMPTY (assuming no other implicit attrs).
             # So all colors fall into the SAME Group Key (empty tuple).
             # So they share the SAME Serial.
             
             # Conclusion:
             # If Group Key is same as existing variant's group key -> Reuse Serial.
             # If Group Key is NEW (e.g. new implicit attr value) -> New Serial?
             
             # In your case A (New Color, Explicit):
             # Group Key is empty (unchanged).
             # So we should REUSE the serial.
             
             current_serial = start_serial # Use the one found from DB
        else:
             current_serial = start_serial

        sorted_group_keys = sorted(groups.keys())
        for g_key in sorted_group_keys:
            # If reusing, we want to map g_key to existing serial if possible
            # But for simplicity in "One SPU One Serial" model (if that's the case):
            group_serials[g_key] = f"{current_serial:02d}"
            
            # Only increment if we are NOT reusing (or if we support multi-serial SPUs and this is a new group)
            # For now, let's assume One SPU = One Serial for simplicity unless groups differ
            if not existing_spu:
                current_serial += 1
            else:
                # If reusing, we keep using the same serial found in DB.
                # This assumes all variants of this SPU share the same serial.
                pass
            
        # 4. Generate Final Codes
        preview_variants = [None] * len(variants_specs)
        
        for g_key, items in groups.items():
            serial = group_serials[g_key]
            
            for idx, specs in items:
                # A. Feature Code
                f_code = CodeBuilderService.generate_sku_feature_code(spu_code, specs, category_id)
                
                # B. System SKU
                base_sku = f"{prefix}{serial}"
                
                suffix_parts = []
                
                relevant_attrs = []
                for k, v in specs.items():
                    defn, is_sku, include = get_attr_props(k)
                    if is_sku and include:
                        relevant_attrs.append((defn.code_weight, defn, v))
                
                relevant_attrs.sort(key=lambda x: x[0])
                
                for _, defn, val in relevant_attrs:
                    code = CodeBuilderService._extract_code_from_options(defn.options, val)
                    
                    if code:
                        # HEURISTIC: "Pair" (2P) does not appear in System SKU Suffix
                        if code == "2P":
                            continue
                        suffix_parts.append(code)
                        
                full_sku = base_sku + "".join(suffix_parts)
                
                preview_variants[idx] = {
                    'sku': full_sku,
                    'feature_code': f_code,
                    'specs': specs
                }
                
        result['variants'] = preview_variants
        return result

    @staticmethod
    def generate_sku_feature_code(spu_code: str, attributes: Dict[str, str], category_id: int = None) -> str:
        """
        生成 SKU 特征码 (业务可读码)
        策略: SPU_CODE + Attr1Code + Attr2Code ...
        
        Change 2024-05: Feature Code 应该包含所有 attribute_scope='sku' 的属性，
        无论 include_in_code 是 True 还是 False (颜色不进短码但要进特征码).
        """
        if not attributes:
            return spu_code
            
        # 1. 查出所有相关属性定义
        attr_keys = list(attributes.keys())
        attr_defs = db.session.execute(
            select(AttributeDefinition)
            .where(AttributeDefinition.key_name.in_(attr_keys))
        ).scalars().all()
        
        # 2. 映射
        def_map = {d.key_name: d for d in attr_defs}
        code_parts = []
        
        # [New] 加载 CategoryAttribute 映射以检查 attribute_scope override
        cat_attr_map = {}
        if category_id:
            from app.models.product import CategoryAttribute
            cat_attrs = db.session.execute(
                select(CategoryAttribute)
                .where(
                    CategoryAttribute.category_id == category_id,
                    CategoryAttribute.attribute_id.in_([d.id for d in attr_defs])
                )
            ).scalars().all()
            # Map by attribute_id for easy lookup
            cat_attr_map = {ca.attribute_id: ca for ca in cat_attrs}
        
        # 3. 提取代码
        for key, val_label in attributes.items():
            defn = def_map.get(key)
            if not defn:
                continue

            # Determine scope
            is_sku_scope = True # Default for variant specs?
            if defn.id in cat_attr_map:
                scope = cat_attr_map[defn.id].attribute_scope
                if scope == 'spu':
                    is_sku_scope = False
            
            # Feature Code MUST include all SKU scope attributes
            if not is_sku_scope:
                continue
                
            code_val = CodeBuilderService._extract_code_from_options(defn.options, val_label)
            if code_val:
                code_parts.append((defn.code_weight, code_val))
        
        # 4. 排序 (Sort by weight)
        code_parts.sort(key=lambda x: x[0])
        
        # 5. 拼接
        sorted_codes = [x[1] for x in code_parts]
        if not sorted_codes:
            return spu_code
            
        return f"{spu_code}-" + "-".join(sorted_codes)

    @staticmethod
    def _extract_code_from_options(options: List, label: str) -> Optional[str]:
        """辅助: 提取属性值的代码 (Chrome -> CH)"""
        if not label:
            return None
            
        # 归一化输入
        clean_label = str(label).strip()
        upper_label = clean_label.upper()
        
        # --- Heuristics (Hardcoded Rules for L2.0) ---
        # Position
        if "LEFT" in upper_label or "DRIVER" in upper_label or "左" in upper_label:
            return "D"
        if "RIGHT" in upper_label or "PASSENGER" in upper_label or "右" in upper_label:
            return "P"
        if "PAIR" in upper_label or "SET" in upper_label or "对" in upper_label:
            return "2P" # For Feature Code. For SKU Suffix, caller needs to handle if it should be empty.
            
        # Color Defaults (if not in options)
        if upper_label == "BLACK": return "BK"
        if upper_label == "CHROME": return "CH"
        if upper_label == "RED": return "RD"
        if upper_label == "SMOKED": return "SM"
        
        if not options:
            # 无配置，默认取前5位大写 (Rule: 5 chars max)
            return upper_label.replace(" ", "")[:5]
            
        for opt in options:
            # 兼容 {"label": "x", "code": "y"}
            if isinstance(opt, dict):
                if str(opt.get("label")).upper() == upper_label or str(opt.get("value")).upper() == upper_label:
                    # 优先取 code，没有则自动生成
                    code = opt.get("code")
                    if code:
                        return str(code)
                    return upper_label.replace(" ", "")[:5]
            # 兼容 "x" 字符串列表
            elif isinstance(opt, str):
                if str(opt).upper() == upper_label:
                    return upper_label.replace(" ", "")[:5]
        
        # 选项外的值
        return upper_label.replace(" ", "")[:5]
