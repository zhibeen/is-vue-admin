<script lang="ts" setup>
import { ref, watch, computed, onMounted, h } from 'vue';
import { Card, Form, Select, Input, InputNumber, Switch, Row, Col, Button, message, Cascader, Modal, Divider, Tag, Table, Popconfirm, Alert } from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import type { Category, TaxCategory, CategoryAttributeMapping, VehicleNode, Product as ProductModel } from '#/api/core/product';
import { getCategoriesApi, getTaxCategories, createProduct, getAllCategoryAttributesMappingsApi, previewProductCodesApi, getProductListApi, getYearsApi } from '#/api/core/product';
import { getDictsApi } from '#/api/system/dict';
import VehicleCascader from './components/VehicleCascader.vue'; // Import Component
import { useDebounceFn } from '@vueuse/core';

// --- Form State ---
const formState = ref({
  category: [] as string[], // Cascader value array
  isSPULocked: false, // New: Lock SPU info when loading existing data
  
  // SPU Identity (Metadata)
  // brand_id: undefined as number | undefined, // Removed legacy
  
  // New: Vehicle Cascader Path
  vehiclePath: [] as number[],
  vehicleCodes: {} as Record<string, string>, // Store codes: { make: '01', model: '05' }
  vehicleReadablePath: [] as any[], // Store full node objects for naming
  
  // Manual Year Range Override
  yearRange: {
      start: undefined as number | undefined,
      end: undefined as number | undefined,
      enabled: false // Show manual range inputs
  },
  
  // Dynamic SPU Params (stored flat here for easy v-model, will be packed on save)
  spuParams: {} as Record<string, any>,
  
  name: '',
  
  // SKU Config (Moved to variants)
  // skuSuffix: undefined as string | undefined,
  
  // SERC Fields
  declared_name: '',
  declared_unit: 'PCS',
  hs_code_id: undefined,
  tax_category_id: undefined as number | undefined,
  
  specs: {
      length: 0,
      width: 0,
      height: 0,
      weight: 0
  },
  
  dynamicAttrs: {} as Record<string, any>,
  
  // Mock Data (Removed: Driven by API now)
});

// --- Data Sources ---
const categories = ref<Category[]>([]);
const skuSuffixOptions = ref<{ label: string; value: string }[]>([]); // New Dict Options
const taxCategories = ref<TaxCategory[]>([]);
const categoryAttributeMappings = ref<CategoryAttributeMapping[]>([]);
// const vehicleTree = ref<VehicleNode[]>([]); // Removed: Async Loading in Component


// --- Variants State ---
interface VariantRow {
    key: number;
    suffix: string; // SKU Suffix (Legacy, kept for type compat)
    name_suffix: string; // e.g. 左侧
    price: number;
    cost_price: number;
    weight: number;
    _specs?: Record<string, any>;
    sku?: string; // New: Server generated
    feature_code?: string; // New: Server generated
    is_existing?: boolean; // New: Flag for locked variants
}

const variants = ref<VariantRow[]>([
    { key: Date.now(), suffix: '', name_suffix: '', price: 0, cost_price: 0, weight: 0, sku: '', feature_code: '', is_existing: false }
]);

const addVariant = () => {
    variants.value.push({
        key: Date.now(),
        suffix: '',
        name_suffix: '',
        price: 0,
        cost_price: 0,
        weight: formState.value.specs.weight || 0,
        sku: 'Pending...',
        feature_code: 'Pending...',
        is_existing: false
    });
    // Trigger preview update immediately
    fetchPreviewData();
};

const removeVariant = (index: number) => {
    variants.value.splice(index, 1);
};

// --- Computed Helpers ---
const currentCategory = computed(() => {
    if (!formState.value.category || formState.value.category.length === 0) return null;
    const leafId = formState.value.category[formState.value.category.length - 1];
    
    const findNode = (nodes: Category[], id: string | undefined): Category | null => {
        if (!id) return null;
        for (const node of nodes) {
            if (node.id === id) return node;
            if (node.children) {
                const found = findNode(node.children, id);
                if (found) return found;
            }
        }
        return null;
    };
    return findNode(categories.value, leafId);
});

// Helper: Resolve effective spu_config (Recursive)
const effectiveSpuConfig = computed(() => {
    const cat = currentCategory.value;
    if (!cat) return null;
    
    // Recursive lookup
    let config = null;
    let curr = cat;
    
    const findParent = (nodes: Category[], id: string): Category | null => {
        for (const node of nodes) {
            if (node.children) {
                if (node.children.some(c => c.id === id)) return node;
                const found = findParent(node.children, id);
                if (found) return found;
            }
        }
        return null;
    };

    while (curr) {
        if (curr.spu_config && (curr.spu_config.fields || curr.spu_config.vehicle_link)) {
            config = curr.spu_config;
            break;
        }
        if (curr.parent_id) {
            curr = findParent(categories.value, curr.id);
        } else {
            curr = null;
        }
    }
    return config;
});

// Determine if we should show Vehicle Cascader
const vehicleLinkConfig = computed(() => {
    const config = effectiveSpuConfig.value;
    if (config?.vehicle_link?.enabled) {
        return config.vehicle_link;
    }
    
    // Fallback: Default to Vehicle behavior if business_type is 'vehicle' and no explicit config
    if ((currentCategory.value?.business_type === 'vehicle' || !currentCategory.value?.business_type) && !config?.fields) {
        return { 
            enabled: true, 
            levels: ['brand', 'model', 'year'] // Default strict chain
        };
    }
    
    return null;
});

// Determine if vehicle selection is complete based on config
const isVehicleSelectionComplete = computed(() => {
    if (!vehicleLinkConfig.value) return true;
    const requiredLevels = vehicleLinkConfig.value.levels.length;
    const currentPath = formState.value.vehiclePath || [];
    
    // If manual year range is enabled and valid, we consider it complete if we have selected up to Model
    // (Assuming 'year' is the last required level)
    if (formState.value.yearRange.enabled && formState.value.yearRange.start && formState.value.yearRange.end) {
        const lastRequired = vehicleLinkConfig.value.levels[vehicleLinkConfig.value.levels.length - 1];
        if (lastRequired === 'year') {
             return currentPath.length >= (requiredLevels - 1);
        }
    }
    
    // Standard check
    return currentPath.length >= requiredLevels;
});

// Human readable rule hint
const vehicleRuleHint = computed(() => {
    if (!vehicleLinkConfig.value) return '';
    const levels = vehicleLinkConfig.value.levels;
    const levelNames = {
        'make': '品牌 (Make)',
        'model': '车型 (Model)',
        'platform': '底盘代号 (Platform)',
        'year': '年份 (Year)',
        'series': '车系 (Series)'
    };
    
    const chain = levels.map(l => levelNames[l] || l).join(' > ');
    
    return {
        message: `当前分类要求车型精度: ${chain}`,
        description: '请务必完整选择每一层级，否则生成的 SPU 编码将不完整，且无法正确匹配车型数据。',
        status: isVehicleSelectionComplete.value ? 'success' : 'warning'
    };
});

// NEW: Compute SPU Schema Fields (Non-Vehicle)
const spuSchema = computed(() => {
    // If vehicle link is active, we don't use schema fields for those parts
    if (vehicleLinkConfig.value) {
        return [];
    }
    
    const config = effectiveSpuConfig.value;
    if (config?.fields) {
        return config.fields;
    }
    
    // Fallback: General Type
    return [
        { key: 'series', label: '系列/规格 (Series)', type: 'input', required: true, placeholder: 'PRO' }
    ];
});

// Helper to find node in vehicle tree - Removed as we use VehicleCascader events

// Handle Vehicle Change from Component
const handleVehicleChange = async (val: any[], selectedOptions: any[]) => {
    formState.value.vehiclePath = val;
    formState.value.vehicleReadablePath = selectedOptions; // Store full nodes
    
    // Clear old params
    const levels = ['make', 'brand', 'series', 'model', 'platform', 'year'];
        levels.forEach(k => delete formState.value.spuParams[k]);
    
    // Reset Year Range State
    formState.value.yearRange = { start: undefined, end: undefined, enabled: false };

    if (!val || val.length === 0) {
        return;
    }

    const lastNode = selectedOptions[selectedOptions.length - 1];

    // 1. Map Explicit Levels from Path
    selectedOptions.forEach((node, index) => {
        if (node.level_type) {
            formState.value.spuParams[node.level_type] = node.abbreviation || node.code;
            if (node.code) formState.value.vehicleCodes[node.level_type] = node.code;
            
            // Handle aliases
            if (node.level_type === 'make') {
                formState.value.spuParams['brand'] = node.abbreviation || node.code;
                if (node.code) formState.value.vehicleCodes['brand'] = node.code;
            }
        }
    });

    // 2. Year Logic: Check if we stopped at Model/Platform
    if (lastNode.level_type === 'year') {
        // Explicit single year selected
        formState.value.spuParams['year'] = lastNode.abbreviation || lastNode.code;
    } else {
        // Stopped at Model (or Platform) - Need to fetch/check years for Range
        // If children are already loaded (via Cascader expansion), use them.
        // If not, fetch them now.
        
        let yearsData = lastNode.children || [];
        
        if (yearsData.length === 0 && (lastNode.level_type === 'model' || lastNode.level_type === 'platform')) {
             try {
                 const res = await getYearsApi(lastNode.value);
                 yearsData = (res as any).data || res || [];
             } catch (e) {
                 console.error('Failed to auto-fetch years', e);
             }
        }
        
        if (yearsData.length > 0) {
            const firstChild = yearsData[0];
            // Check if looks like year (4 digits) or level_type='year'
            if (firstChild.level_type === 'year' || /^\d{4}$/.test(firstChild.label || firstChild.name)) {
                formState.value.yearRange.enabled = true;
                
                // Auto-detect default range
                const years = yearsData.map((c: any) => parseInt(c.label || c.name)).filter((n: number) => !isNaN(n));
                if (years.length > 0) {
                    formState.value.yearRange.start = Math.min(...years);
                    formState.value.yearRange.end = Math.max(...years);
                    updateYearParamFromRange();
                }
            }
        }
    }
};

// Update SPU 'year' param when manual range changes
const updateYearParamFromRange = () => {
    const { start, end } = formState.value.yearRange;
    if (start && end) {
        const s = String(start).slice(-2);
        const e = String(end).slice(-2);
        // Format: YY-YY (e.g. 05-12)
        formState.value.spuParams['year'] = (s === e) ? s : `${s}-${e}`;
        } else {
        delete formState.value.spuParams['year'];
    }
};

// Auto-generate Product Name (Improved Rule Based)
const generateProductName = () => {
    const cat = currentCategory.value;
    if (!cat) {
        message.warning('请先选择产品分类');
        return;
    }
    
    // --- 1. Vehicle Info Generation ---
    let vehicleString = '';
    const pathNodes = formState.value.vehicleReadablePath || [];
    
    if (pathNodes.length > 0) {
        // Collect all parts that are NOT pure years (e.g. BMW, 3-Series, E90)
        // We use a regex to filter out "2005", "2011" etc.
        const modelParts = pathNodes
            .filter((node: any) => !/^\d{4}$/.test(node.label || node.name)) // Filter out year nodes
            .map((node: any) => node.label || node.name);
            
        vehicleString = modelParts.join(' '); // e.g. "BMW 3-Series E90"
        
        // Add Year Range
        let yearString = '';
        if (formState.value.yearRange.enabled && formState.value.yearRange.start) {
            // Manual range takes precedence
            yearString = `${formState.value.yearRange.start}-${formState.value.yearRange.end}`;
        } else if (formState.value.spuParams['year']) {
            // Auto-calculated range or single year
            const y = formState.value.spuParams['year'];
            if (y.includes('-')) {
                // Expand "05-11" to "2005-2011"
                const [s, e] = y.split('-');
                yearString = `${s.length===2 ? '20'+s : s}-${e.length===2 ? '20'+e : e}`;
            } else {
                yearString = y.length===2 ? '20'+y : y;
            }
        }
        
        if (yearString) {
            vehicleString += ` ${yearString}`;
        }
        
        if (vehicleString) {
            vehicleString = `适用 ${vehicleString}`;
        }
    } else {
        // Fallback: Use raw params if path is missing (shouldn't happen if cascader is used)
        const brand = formState.value.spuParams['brand'] || formState.value.spuParams['make'];
        const model = formState.value.spuParams['model'];
        if (brand) vehicleString = `适用 ${brand} ${model || ''}`.trim();
    }

    // --- 2. Core Name (Category) ---
    // Try to get 3rd + 4th level name if available
    let coreName = cat.name;
    if (formState.value.category.length >= 2) {
        // Simple name finding logic can be here, but for now leaf name is fine or previous logic
        // Let's stick to leaf name + parent name if we can access it, but simplicity is better.
        // User liked "Category"
    }
    
    // --- 3. Suffix (Attributes) ---
    const attrs: string[] = [];
    rawAttrDefinitions.value.forEach(attr => {
        const val = formState.value.dynamicAttrs[attr.key];
        if (val) {
            if (attr.options) {
                const opt = attr.options.find((o: any) => o.value === val);
                if (opt) attrs.push(opt.label);
            } else {
                attrs.push(String(val));
            }
        }
    });
    const attrSuffix = attrs.join(' ');
    
    // --- 4. Final Combination ---
    // [Core Name] [Attributes] [Vehicle Info]
    // e.g. "LED前照灯 左侧 适用 BMW 3-Series E90 2005-2011"
    const fullName = `${coreName} ${attrSuffix} ${vehicleString}`.trim().replace(/\s+/g, ' ');
    
    formState.value.name = fullName;
    message.success('已自动生成产品名称');
};

// Watch manual inputs to update SPU code
watch(() => [formState.value.yearRange.start, formState.value.yearRange.end], () => {
    if (formState.value.yearRange.enabled) {
        updateYearParamFromRange();
    }
});

// Removed old watcher for vehiclePath as we handle it in event


// Template section update
// spuCodePreview -> previewSpuCode
// skuSystemCodePreview -> (removed, individual rows have skus)
// getRowSkuPreview -> record.sku
// getRowFeaturePreview -> record.feature_code

// --- Attribute Usage Logic ---
const attributeUsage = ref<Record<string, 'spu' | 'sku'>>({});
const skuGenerationState = ref<Record<string, any[]>>({});

// Computed Base Definitions (Raw)
const rawAttrDefinitions = computed(() => {
    const selectedIds = formState.value.category;
    if (!selectedIds || selectedIds.length === 0) return [];
    
    const selectedIdNums = selectedIds.map(id => Number(id));
    
    const relevantMappings = categoryAttributeMappings.value
        .filter(m => selectedIdNums.includes(m.category_id))
        .sort((a, b) => {
            const indexA = selectedIdNums.indexOf(String(a.category_id))
            const indexB = selectedIdNums.indexOf(String(b.category_id))
            if (indexA !== indexB) return indexA - indexB;
            return a.display_order - b.display_order
        });
        
    const uniqueAttrs = new Map();
    relevantMappings.forEach(m => {
        uniqueAttrs.set(m.attribute.key, m);
    });
    
    return Array.from(uniqueAttrs.values()).map(m => {
        const rawOptions = m.attribute.options || [];
        const normalizedOptions = rawOptions.map((opt: any) => {
            if (typeof opt === 'string') return { label: opt, value: opt };
            return opt;
        });

        return {
            ...m.attribute,
            options: normalizedOptions,
            required: m.is_required,
            code_weight: m.attribute.code_weight,
            attribute_scope: m.attribute_scope,
            include_in_code: m.include_in_code // Pass this flag to frontend
        };
    });
});

// Watch raw attrs to init usage
watch(rawAttrDefinitions, (newAttrs) => {
    const newUsage: Record<string, 'spu' | 'sku'> = {};
    newAttrs.forEach(attr => {
        // Prefer user selection if exists, otherwise use attribute_scope from backend config
        if (attributeUsage.value[attr.key]) {
             newUsage[attr.key] = attributeUsage.value[attr.key];
        } else {
             newUsage[attr.key] = (attr as any).attribute_scope === 'sku' ? 'sku' : 'spu';
        }
    });
    attributeUsage.value = newUsage;
}, { immediate: true });

const spuAttributes = computed(() => rawAttrDefinitions.value.filter(attr => attributeUsage.value[attr.key] === 'spu'));
const skuAttributes = computed(() => rawAttrDefinitions.value.filter(attr => attributeUsage.value[attr.key] === 'sku'));

// Helper: Cartesian Product
const cartesian = (args: any[][]) => {
    if (args.length === 0) return [];
    return args.reduce((a, b) => {
        return a.flatMap(d => b.map(e => [d, e].flat()));
    }, [[]] as any[][]);
};

// Helper: Calculate Suffix from Specs based on current rules
const calculateSuffixFromSpecs = (specs: Record<string, any>) => {
    const activeSkuAttrs = skuAttributes.value;
    const skuSuffixParts: string[] = [];
    const featureSuffixParts: string[] = [];
    
    // We need to iterate in the same order as axes to be consistent?
    // Actually generateVariants iterates axes. Here we iterate activeSkuAttrs.
    // Order matters for suffix concatenation.
    
    activeSkuAttrs.forEach(attr => {
        const val = specs[attr.key];
        if (!val) return;
        
        const strVal = String(val).toUpperCase();
        const optDef = attr.options?.find((o: any) => o.value === val);
        const includeInCode = (attr as any).include_in_code !== false;
        
        // 1. System SKU Suffix
        if (includeInCode) {
            let skuCode = '';
            if (attr.key === 'position' || attr.label.includes('位置')) {
                if (strVal.includes('PAIR') || strVal.includes('SET') || strVal.includes('对装')) {
                    skuCode = ''; 
                } else if (strVal.includes('PASSENGER') || strVal.includes('RIGHT') || strVal.includes('右')) {
                    skuCode = 'P'; 
                } else if (strVal.includes('DRIVER') || strVal.includes('LEFT') || strVal.includes('左')) {
                    skuCode = 'D'; 
                } else {
                     skuCode = optDef?.code || strVal.replace(/[^A-Z0-9]/g, '').slice(0, 1);
                }
            } else {
                skuCode = optDef?.code || strVal.replace(/[^A-Z0-9]/g, '').slice(0, 1);
            }
            if (skuCode) skuSuffixParts.push(skuCode);
        }
        
        // 2. Feature Code Suffix
        let featureCode = '';
        if (attr.key === 'position' || attr.label.includes('位置')) {
            if (strVal.includes('PAIR') || strVal.includes('SET') || strVal.includes('对装')) {
                featureCode = '2P'; 
            } else if (strVal.includes('PASSENGER') || strVal.includes('RIGHT') || strVal.includes('右')) {
                featureCode = 'P'; 
            } else if (strVal.includes('DRIVER') || strVal.includes('LEFT') || strVal.includes('左')) {
                featureCode = 'D'; 
            } else {
                 featureCode = optDef?.code || strVal.replace(/[^A-Z0-9]/g, '').slice(0, 1);
            }
        } else {
            featureCode = optDef?.code || strVal.replace(/[^A-Z0-9]/g, '').slice(0, 5); 
        }
        if (featureCode) featureSuffixParts.push(featureCode);
    });
    
    return {
        suffix: skuSuffixParts.join(''),
        feature_suffix: '-' + featureSuffixParts.join('-')
    };
};

// Action: Generate Variants (Incremental Merge Support)
const generateVariants = () => {
    const activeSkuAttrs = skuAttributes.value;
    if (activeSkuAttrs.length === 0) return;

    const axes = activeSkuAttrs.map(attr => ({
        key: attr.key,
        label: attr.label,
        values: skuGenerationState.value[attr.key] || []
    })).filter(axis => axis.values.length > 0);

    if (axes.length === 0) {
        message.warning('请至少选择一个变体属性值');
        return;
    }

    const combos = axes.length === 1 
        ? axes[0].values.map(v => [v]) 
        : cartesian(axes.map(a => a.values));

    // Check for existing locked rows
    const existingRows = variants.value.filter(v => v.is_existing);
    const hasExisting = existingRows.length > 0;

    // Confirm overwrite ONLY if no locked rows exist
    if (!hasExisting && (variants.value.length > 1 || (variants.value.length === 1 && variants.value[0].suffix !== ''))) {
        if (!confirm('重新生成将覆盖现有变体列表，确认继续？')) return;
    }

    const newVariants: VariantRow[] = [];
    let addedCount = 0;

    combos.forEach((combo: any[], idx) => {
        const flatCombo = Array.isArray(combo) ? combo : [combo];
        const specs: Record<string, any> = {};
        axes.forEach((axis, i) => {
             specs[axis.key] = flatCombo[i];
        });
        
        // Smart Merge: Check if this spec combination already exists in locked rows
        const match = existingRows.find(row => {
            if (!row._specs) return false;
            // Check if all generated specs match the row's specs
            // Use String comparison to handle potential type mismatches (e.g. "1" vs 1)
            const isMatch = Object.keys(specs).every(k => {
                const existingVal = row._specs![k];
                const newVal = specs[k];
                // Treat undefined/null as empty string for comparison
                return String(existingVal || '') === String(newVal || '');
            });
            
            if (isMatch) {
                console.log(`[Smart Merge] Match found for`, specs, `in row`, row);
            }
            return isMatch;
        });

        if (match) {
            // Already exists as a locked row, skip adding new one
            return; 
        }
        
        const nameSuffix = flatCombo.map(v => String(v)).join(' ');
        
        // Use helper to calculate suffixes
        const { suffix: codeSuffix, feature_suffix: featureSuffix } = calculateSuffixFromSpecs(specs);

        newVariants.push({
            key: Date.now() + idx + Math.random(),
            suffix: codeSuffix, // For System SKU
            feature_suffix: featureSuffix, // New: For Feature Code
            name_suffix: nameSuffix,
            price: 0,
            cost_price: 0,
            weight: formState.value.specs.weight || 0,
            _specs: specs, // Important: Store specs for API preview
            is_existing: false
        });
        addedCount++;
    });
    
    // Merge: Existing Locked Rows + New Generated Rows
    // We discard any previous non-locked rows (overwrite behavior for new generation), 
    // but keep locked rows (smart merge behavior).
    variants.value = [...existingRows, ...newVariants];
    
    if (hasExisting) {
        message.success(`增量合并完成：保留 ${existingRows.length} 个已有变体，新增 ${addedCount} 个新变体`);
    } else {
        message.success(`已生成 ${newVariants.length} 个变体`);
    }
    
    // Trigger Server Preview Immediately
    fetchPreviewData();
};

// --- Preview Logic (Server Driven) ---
const previewSpuCode = ref('---');
const isPreviewLoading = ref(false);
const spuDuplicateInfo = ref<{ exists: boolean; code: string }>({ exists: false, code: '' });

const loadExistingVariants = async () => {
    if (!spuDuplicateInfo.value.exists || !spuDuplicateInfo.value.code) return;
    
    try {
        loading.value = true;
        const res = await getProductListApi({ q: spuDuplicateInfo.value.code, page: 1, per_page: 1 });
        if (res.items && res.items.length > 0) {
            const product = res.items[0];
            // Only load variants if SPU matches exactly
            if (product.spu_code === spuDuplicateInfo.value.code) {
                 // Map existing variants to UI rows
                 // Note: product.variants usually come from backend. 
                 // We need to check if 'variants' are included in list response or need detail.
                 // Assuming list response includes variants (based on ProductService.list_products options)
                 
                 const existingVariants = (product as any).variants || [];
                 if (existingVariants.length > 0) {
                     if (!confirm(`找到 ${existingVariants.length} 个已有 SKU。是否加载并覆盖当前列表？`)) {
                         loading.value = false;
                         return;
                     }
                     
                     variants.value = existingVariants.map((v: any) => {
                         // Calculate expected suffix from specs for display consistency
                         const { suffix } = v.specs ? calculateSuffixFromSpecs(v.specs) : { suffix: '' };
                         
                         return {
                             key: v.id || Date.now() + Math.random(),
                             suffix: suffix, // Use calculated suffix
                             name_suffix: v.specs?._variant_name_suffix || '',
                             price: v.price,
                             cost_price: v.cost_price,
                             weight: v.weight,
                             sku: v.sku,
                             feature_code: v.feature_code,
                             _specs: v.specs,
                             is_existing: true // Lock these rows
                         };
                     });
                     
                     // Lock SPU Info
                     formState.value.name = product.name;
                     formState.value.isSPULocked = true;
                     
                     // Restore SPU Attributes & Lock
                     if (product.attributes) {
                         // Merge with existing to keep keys, but overwrite values
                         formState.value.dynamicAttrs = {
                             ...formState.value.dynamicAttrs,
                             ...product.attributes
                         };
                     }
                     
                     message.success('已加载现有变体');
                 } else {
                     message.warning('该 SPU 下暂无变体');
                 }
            } else {
                 message.warning('未找到完全匹配的 SPU');
            }
        } else {
            message.warning('未找到该 SPU 数据');
        }
    } catch (e) {
        console.error(e);
        message.error('加载失败');
    } finally {
        loading.value = false;
    }
};

const fetchPreviewData = async () => {
    const categoryId = formState.value.category?.[formState.value.category.length - 1];
    if (!categoryId) return;
    
    // Reset Duplicate Info on new fetch attempt
    spuDuplicateInfo.value = { exists: false, code: '' };
    
    // Construct simplified variants for preview
    // Only send variant-specific specs. Common attrs are sent via metadata if needed.
    const simplifiedVariants = variants.value.map(v => ({
        ...(v._specs || {}),
    }));
    
    if (simplifiedVariants.length === 0) {
        simplifiedVariants.push({});
    }

    try {
        isPreviewLoading.value = true;
        
        // Merge SPU params with Vehicle Codes AND Common Attributes for backend logic
        const metadata = {
            ...formState.value.spuParams,
            ...formState.value.dynamicAttrs, // Include common attrs here for SPU template
            make_code: formState.value.vehicleCodes['make'] || formState.value.vehicleCodes['brand'],
            model_code: formState.value.vehicleCodes['model'],
        };

        const res = await previewProductCodesApi({
            category_id: Number(categoryId),
            spu_coding_metadata: metadata,
            variants: simplifiedVariants
        });
        
        previewSpuCode.value = res.spu_code;
        
        // Update variants with generated codes
        if (res.variants && res.variants.length === variants.value.length) {
            res.variants.forEach((pv: any, idx: number) => {
                if (pv) {
                    variants.value[idx].sku = pv.sku;
                    variants.value[idx].feature_code = pv.feature_code;
                }
            });
        }
    } catch (e: any) {
         // --- 新增：处理 SPU 重复警告 ---
         const errCode = e.response?.data?.code || e.code;
         const errData = e.response?.data?.data || e.data; // 获取预览数据

         if (errCode === 30003) { // PRODUCT_SPU_CODE_EXIST
             // message.warning('生成的 SPU 编码已存在，请检查是否重复创建'); // Removed
             
             // Set Duplicate State
             if (errData && errData.spu_code) {
                 spuDuplicateInfo.value = { exists: true, code: errData.spu_code };
                 previewSpuCode.value = errData.spu_code; // Show the code even if duplicate
                 
                 // Still update variants preview
                 if (errData.variants && errData.variants.length === variants.value.length) {
                     errData.variants.forEach((pv: any, idx: number) => {
                         if (pv) {
                             variants.value[idx].sku = pv.sku;
                             variants.value[idx].feature_code = pv.feature_code;
                         }
                     });
                 }
             }
             return; // 已处理，退出
         }
         // -----------------------------
        
        console.error("Preview failed", e);
    } finally {
        isPreviewLoading.value = false;
    }
};

const updatePreview = useDebounceFn(fetchPreviewData, 500);

// Watchers to trigger preview
watch(() => formState.value.spuParams, updatePreview, { deep: true });
watch(() => formState.value.category, updatePreview);

// --- Lifecycle & Watchers ---
    onMounted(async () => {
        // 1. Critical Base Data (Blocking UI mostly for category selection)
        try {
            const [cats, dicts, taxes, mappings] = await Promise.all([
                getCategoriesApi(),
                getDictsApi(),
                getTaxCategories(),
                getAllCategoryAttributesMappingsApi()
            ]);
            categories.value = cats;
            taxCategories.value = taxes;
            categoryAttributeMappings.value = mappings;
            
            // Load Suffix Dict
            const dict = dicts.find((d: any) => d.code === 'sku_suffix');
            if (dict && dict.value_options) {
                skuSuffixOptions.value = dict.value_options.map((o: any) => ({
                    label: o.label,
                    value: o.value
                }));
            }
        } catch (e) {
            message.error('Failed to load base data');
            console.error(e);
        }
    });

watch(() => formState.value.category, async (newVal) => {
    formState.value.dynamicAttrs = {};
    // Reset SPU Params too
    formState.value.spuParams = {};
    formState.value.vehiclePath = []; // Reset vehicle path
    
    if (newVal && newVal.length > 0) {
        rawAttrDefinitions.value.forEach((attr) => {
            if(attr.type === 'boolean') {
                formState.value.dynamicAttrs[attr.key] = false;
            }
        });
    }
});

const loading = ref(false);

const handleSave = async () => {
    try {
        loading.value = true;
        // Construct payload
        // Filter out frontend-only fields by cherry-picking needed fields
        const payload: any = {
            name: formState.value.name,
            category_id: formState.value.category?.[formState.value.category.length - 1],
            attributes: formState.value.dynamicAttrs,
            
            // Map params to spu_coding_metadata or individual fields if backend requires
            // Backend Schema currently expects 'brand_code' (optional) and others in attributes?
            // Actually ProductCreateSchema just has ProductBaseSchema fields.
            // Let's pass spuParams as metadata if backend supports it, or merge into attributes?
            // Current backend Schema doesn't have 'spu_coding_metadata' field explicitly defined in Input!
            // We need to update backend Schema or pack it.
            // For now, let's assume backend takes 'attributes' for general props.
            
            // SERC
            declared_name: formState.value.declared_name, // Not in BaseSchema? Check backend.
            declared_unit: formState.value.declared_unit,
            
            // Construct Variants
            variants: variants.value.map(v => ({
                sku: v.sku, // Use Server Generated SKU directly
                feature_code: v.feature_code, // Use Server Generated Feature Code
                
                // Specs for variant (Only Variant Specific Specs + Suffix)
                specs: { 
                    ...(v._specs || {}),
                    _variant_name_suffix: v.name_suffix 
                },
                
                quality_type: 'Aftermarket',
                price: v.price,
                cost_price: v.cost_price,
                weight: v.weight || formState.value.specs.weight,
                
                hs_code_id: formState.value.hs_code_id,
                declared_name: formState.value.declared_name,
                declared_unit: formState.value.declared_unit
            })),
        };
        
        // Pass SPU Params (Make, Model, Year codes) via a special field if backend expects it
        // Ensure we send the same metadata structure as the preview API
        const spuMetadata = {
            ...formState.value.spuParams,
            make_code: formState.value.vehicleCodes['make'] || formState.value.vehicleCodes['brand'],
            model_code: formState.value.vehicleCodes['model'],
        };
        
        console.log("Submitting SPU Metadata:", spuMetadata); // Debug
        
        // Validation: Ensure Metadata is present for Vehicle Categories
        if (vehicleLinkConfig.value && (!spuMetadata.make_code || !spuMetadata.model_code)) {
             message.error('车型数据不完整，无法生成有效 SPU 编码。请重新选择适用车型。');
             loading.value = false;
             return;
        }

        payload.spu_coding_metadata = spuMetadata;
        
        if (!payload.category_id) {
            message.error('请选择产品分类');
            return;
        }

        const res = await createProduct(payload); 
        
        // Detailed Success Message based on new stats structure
        const stats = (res as any).stats || {};
        const action = (res as any).action;
        const spuCode = (res as any).spu_code;
        
        Modal.success({
            title: action === 'merged' ? '商品增量更新成功' : '商品创建成功',
            width: 600,
            content: h('div', {}, [
                h('div', { class: 'text-base font-bold mb-2 text-green-600' }, `SPU: ${spuCode}`),
                h('div', { class: 'space-y-1 text-gray-600' }, [
                    h('div', `本次处理变体总数: ${stats.total || 0}`),
                    h('div', [
                        h('span', '新增: '),
                        h('strong', { class: 'text-green-600' }, stats.new || 0),
                        h('span', ' 个')
                    ]),
                    h('div', [
                        h('span', '更新: '),
                        h('strong', { class: 'text-blue-600' }, stats.updated || 0),
                        h('span', ' 个')
                    ]),
                    h('div', [
                        h('span', '已有(忽略): '),
                        h('strong', { class: 'text-gray-500' }, stats.existing || 0),
                        h('span', ' 个')
                    ]),
                ]),
                // Show list of new variants if any
                (res as any).new_variants && (res as any).new_variants.length > 0 ? h('div', { class: 'mt-4 p-2 bg-gray-50 rounded border' }, [
                    h('div', { class: 'text-xs text-gray-500 mb-1' }, '新增 SKU 列表:'),
                    h('div', { class: 'grid grid-cols-2 gap-2' }, 
                        (res as any).new_variants.map((sku: string) => h('Tag', { color: 'green' }, sku))
                    )
                ]) : null
            ]),
            okText: '继续',
            onOk() { 
                // Do NOT auto-reset. Let user decide.
                // resetForm(); 
            },
        });
        
    } catch (e: any) {
        console.error(e);
        message.error(e.message || '创建失败');
    } finally {
        loading.value = false;
    }
};

const resetForm = () => {
    formState.value.name = '';
    formState.value.category = []; // Reset Category
    formState.value.spuParams = {};
    formState.value.specs = { length: 0, width: 0, height: 0, weight: 0 };
    formState.value.dynamicAttrs = {};
    // formState.value.mockSerial = null;
    formState.value.vehiclePath = []; // Reset path
    formState.value.vehicleCodes = {};
    formState.value.vehicleReadablePath = [];
    formState.value.yearRange = { start: undefined, end: undefined, enabled: false };
    
    // Unlock State
    formState.value.isSPULocked = false;
    spuDuplicateInfo.value = { exists: false, code: '' };
    previewSpuCode.value = '---';
    attributeUsage.value = {};
    skuGenerationState.value = {};
    
    variants.value = [{ key: Date.now(), suffix: '', name_suffix: '', price: 0, cost_price: 0, weight: 0, sku: '', feature_code: '', is_existing: false }];
};
</script>

<template>
  <Page title="创建新产品 (V2.0 Schema)">
    <div class="max-w-5xl mx-auto space-y-4">
      
      <!-- 1. Classification & Identity -->
      <Card title="1. 产品身份 (SPU Identity)" :bordered="false">
        <Form layout="vertical">
          <Row :gutter="16">
            <Col :span="12">
              <Form.Item label="产品分类" required>
                <Cascader 
                    v-model:value="formState.category" 
                    :options="categories" 
                    :field-names="{ label: 'name', value: 'id', children: 'children' }"
                    placeholder="请选择分类" 
                />
              </Form.Item>
            </Col>
            
            <Col :span="12">
              <!-- New: Vehicle Cascader (Explicit Level Chain) -->
              <div v-if="vehicleLinkConfig">
                   <Form.Item 
                        label="适用车型 (Vehicle Identity)" 
                        required 
                        :validate-status="isVehicleSelectionComplete ? '' : 'warning'"
                        :help="isVehicleSelectionComplete ? '' : '请继续选择下一级...'"
                   >
                     <VehicleCascader 
                         v-model:value="formState.vehiclePath" 
                         @change="handleVehicleChange"
                         class="mb-2"
                     />

                     <Alert 
                        v-if="vehicleRuleHint"
                        :message="vehicleRuleHint.message" 
                        :type="vehicleRuleHint.status" 
                        show-icon 
                        class="mb-2"
                        style="padding: 6px 12px; font-size: 12px;"
                     >
                        <template #description v-if="!isVehicleSelectionComplete">
                            <span class="text-xs text-gray-500">{{ vehicleRuleHint.description }}</span>
                        </template>
                     </Alert>
                     
                     <!-- Manual Year Range Override -->
                     <div v-if="formState.yearRange.enabled" class="p-3 bg-gray-50 border border-gray-200 rounded">
                         <div class="text-xs text-gray-500 mb-1 flex justify-between">
                             <span>适用年份区间 (Year Range)</span>
                             <span class="text-blue-600 cursor-pointer" @click="formState.yearRange.enabled = false; formState.vehiclePath = []">重置</span>
                         </div>
                         <div class="flex items-center gap-2">
                             <InputNumber 
                                 v-model:value="formState.yearRange.start" 
                                 :min="1900" :max="2099" 
                                 placeholder="Start"
                                 class="flex-1" 
                             />
                             <span class="text-gray-400">-</span>
                             <InputNumber 
                                 v-model:value="formState.yearRange.end" 
                                 :min="1900" :max="2099" 
                                 placeholder="End"
                                 class="flex-1"
                             />
                         </div>
                         <div class="text-xs text-gray-400 mt-1">
                            如果不完全适配该车型所有年份，请手动修改区间。
                         </div>
                     </div>
                   </Form.Item>
              </div>
              <div v-else>
                   <!-- Fallback if not vehicle -->
                   <div class="text-gray-400 p-2">无需选择品牌/车型</div>
              </div>
            </Col>
          </Row>

          <!-- Dynamic SPU Fields (Only for Non-Vehicle or if explicitly configured) -->
          <div v-if="spuSchema.length > 0" class="bg-gray-50 p-4 rounded mb-4">
              <Row :gutter="16">
                  <Col :span="8" v-for="field in spuSchema" :key="field.key">
                      <Form.Item :label="field.label" :required="field.required" :tooltip="field.placeholder">
                          
                          <!-- Select Type -->
                          <Select v-if="field.type === 'select'"
                                  v-model:value="formState.spuParams[field.key]"
                                  :placeholder="field.placeholder || '请选择'">
                              <Select.Option v-for="opt in field.options" :key="typeof opt==='string'?opt:opt.value" :value="typeof opt==='string'?opt:opt.value">
                                  {{ typeof opt==='string'?opt:opt.label }}
                              </Select.Option>
                          </Select>
                          
                          <!-- Number Type -->
                          <InputNumber v-else-if="field.type === 'number'"
                                       v-model:value="formState.spuParams[field.key]"
                                       class="w-full"
                                       :placeholder="field.placeholder" />
                                       
                          <!-- Default Input -->
                          <Input v-else 
                                 v-model:value="formState.spuParams[field.key]" 
                                 :placeholder="field.placeholder" 
                                 style="text-transform: uppercase" />
                      </Form.Item>
                  </Col>
              </Row>
          </div>

          <!-- Preview SPU Code -->
          <div class="flex items-center gap-4 bg-blue-50 p-3 rounded border border-blue-100 relative">
              <div class="text-gray-500">SPU 特征码预览:</div>
              <div class="text-xl font-mono font-bold" :class="spuDuplicateInfo.exists ? 'text-red-600' : 'text-blue-700'">
                  <span v-if="isPreviewLoading" class="text-gray-400 text-sm">Loading...</span>
                  <span v-else>{{ previewSpuCode }}</span>
              </div>
              <Tag color="blue" v-if="!spuDuplicateInfo.exists">逻辑标识</Tag>
              
              <!-- Duplicate Warning & Action -->
              <div v-if="spuDuplicateInfo.exists" class="flex items-center gap-2 ml-auto">
                  <Tag color="red">已存在</Tag>
                  <Button size="small" type="primary" danger @click="loadExistingVariants" :loading="loading">
                      加载已有变体
                  </Button>
              </div>
          </div>
        </Form>
      </Card>

      <!-- 2. Basic Info -->
      <Card title="2. 基础信息" :bordered="false">
           <Form layout="vertical">
               <Form.Item label="产品名称" required>
                   <div class="flex gap-2">
                   <Input v-model:value="formState.name" placeholder="官方产品名称" :disabled="formState.isSPULocked" />
                       <Button @click="generateProductName" type="dashed" :disabled="formState.isSPULocked">
                           ✨ 自动生成
                       </Button>
                   </div>
                   <div class="text-xs text-gray-400 mt-1">
                       格式: [品类] + [属性] + [适用车型年份]
                   </div>
               </Form.Item>
           </Form>
       </Card>

      <!-- 3. Attributes & SKU -->
      <Card title="3. 属性与变体 (SKU)" :bordered="false">
          <!-- A. Attribute Usage Configuration -->
          <div v-if="rawAttrDefinitions.length > 0" class="mb-6 p-4 bg-gray-50 rounded border border-gray-200">
                <div class="mb-3 font-medium text-gray-700">变体规格配置 (Variant Configuration)</div>
                <div class="text-xs text-gray-500 mb-2">点击标签可切换属性用途：<Tag color="blue">蓝色</Tag>为变体属性，<Tag>灰色</Tag>为公共属性</div>
                <div class="flex flex-wrap gap-2">
                    <div 
                        v-for="attr in rawAttrDefinitions" 
                        :key="attr.key"
                        class="cursor-pointer select-none"
                        @click="attributeUsage[attr.key] = attributeUsage[attr.key] === 'sku' ? 'spu' : 'sku'"
                    >
                        <Tag 
                            :color="attributeUsage[attr.key] === 'sku' ? 'blue' : 'default'"
                            class="m-0 text-sm py-1 px-3 border transition-all"
                            :class="attributeUsage[attr.key] === 'sku' ? 'border-blue-300 font-medium' : 'border-gray-300'"
                        >
                            <span class="mr-1">{{ attributeUsage[attr.key] === 'sku' ? '★' : '•' }}</span>
                            {{ attr.label }}
                        </Tag>
                    </div>
                </div>
          </div>

          <!-- B. Common Attributes (SPU Specs) -->
          <div class="mb-6">
              <div class="text-base font-bold mb-4 border-l-4 border-blue-500 pl-3">公共属性 (SPU Specs)</div>
              <div v-if="spuAttributes.length === 0" class="text-gray-400 pl-4 mb-4 text-sm">
                  {{ rawAttrDefinitions.length > 0 ? '所有属性均已被设为变体属性' : '暂无公共属性 (请先选择分类)' }}
              </div>
              <Form layout="vertical" v-else>
                  <Row :gutter="16">
                      <Col :span="8" v-for="attr in spuAttributes" :key="attr.key">
                          <Form.Item :label="attr.label" :name="['dynamicAttrs', attr.key]" :required="attr.required">
                              <Select v-if="attr.options && attr.options.length > 0" 
                                      v-model:value="formState.dynamicAttrs[attr.key]"
                                      :disabled="formState.isSPULocked"
                                      show-search allow-clear :placeholder="'选择' + attr.label">
                                  <Select.Option v-for="opt in attr.options" :key="opt.value" :value="opt.value">
                                      {{ opt.label }} <span v-if="opt.code" class="text-gray-400 text-xs">({{opt.code}})</span>
                                  </Select.Option>
                              </Select>
                              <Input v-else v-model:value="formState.dynamicAttrs[attr.key]" :placeholder="'输入' + attr.label" :disabled="formState.isSPULocked" />
                          </Form.Item>
                      </Col>
                  </Row>
              </Form>
          </div>
          
          <Divider />
          
          <!-- C. Variant Generator -->
          <div class="mb-6" v-if="skuAttributes.length > 0">
               <div class="text-base font-bold mb-4 border-l-4 border-orange-500 pl-3 flex items-center justify-between">
                   <span>变体生成器 (Variant Generator)</span>
               </div>
               
               <div class="bg-orange-50 p-4 rounded border border-orange-100 mb-4">
                   <Row :gutter="16">
                       <Col :span="8" v-for="attr in skuAttributes" :key="attr.key">
                           <Form.Item :label="attr.label" required>
                               <Select 
                                   v-model:value="skuGenerationState[attr.key]"
                                   mode="multiple"
                                   placeholder="选择变体值 (可多选)"
                                   style="width: 100%"
                                   :options="attr.options"
                                   :field-names="{label:'label', value:'value'}"
                               />
                           </Form.Item>
                       </Col>
                   </Row>
                   <div class="flex justify-end mt-2">
                       <Button type="primary" @click="generateVariants">
                           <span class="mr-1">⚡</span> 自动生成 SKU 列表
                       </Button>
                   </div>
               </div>
          </div>
          
          <!-- D. Variants Table -->
          <div>
              <div class="text-base font-bold mb-4 flex justify-between items-center">
                  <span>SKU 变体列表</span>
                  <div class="text-xs font-normal text-gray-500">
                      <!-- Removed Base SKU preview as it is variant specific -->
                  </div>
              </div>
              
              <Table :dataSource="variants" :pagination="false" row-key="key" size="small" bordered>
                  <!-- New: Dynamic Spec Columns -->
                  <Table.Column 
                      v-for="attr in skuAttributes" 
                      :key="attr.key" 
                      :title="attr.label"
                      width="12%"
                  >
                      <template #default="{ record }">
                           <!-- Try to map value to label if possible -->
                           <span class="text-xs text-gray-600">
                               {{ 
                                   (attr.options && record._specs && attr.options.find((o: any) => o.value === record._specs[attr.key])?.label) 
                                   || (record._specs ? record._specs[attr.key] : '-') 
                               }}
                           </span>
                      </template>
                  </Table.Column>

                  <Table.Column title="变体名称后缀" dataIndex="name_suffix" width="15%">
                      <template #default="{ record }">
                          <Input v-model:value="record.name_suffix" placeholder="如：左侧 / 套装" :disabled="record.is_existing" />
                      </template>
                  </Table.Column>
                  
                  <Table.Column title="属性后缀 (Suffix)" dataIndex="suffix" width="10%">
                      <template #default="{ record }">
                          <Input v-model:value="record.suffix" placeholder="DWD" disabled />
                      </template>
                  </Table.Column>

                  <Table.Column title="System SKU 预览" key="sku_preview" width="20%">
                      <template #default="{ record }">
                          <span v-if="isPreviewLoading" class="text-gray-300 text-xs">Updating...</span>
                          <Tag v-else :color="record.is_existing ? 'green' : 'orange'">
                              {{ record.sku || 'Pending' }}
                              <span v-if="record.is_existing" class="ml-1 text-xs">✔</span>
                          </Tag>
                      </template>
                  </Table.Column>

                  <Table.Column title="Feature Code 预览" key="feature_preview" width="25%">
                      <template #default="{ record }">
                          <span v-if="isPreviewLoading" class="text-gray-300 text-xs">Updating...</span>
                          <Tag v-else :color="record.is_existing ? 'green' : 'blue'">
                              {{ record.feature_code || 'Pending' }}
                          </Tag>
                      </template>
                  </Table.Column>

                  <Table.Column title="操作" width="80px" align="center">
                      <template #default="{ index, record }">
                          <Popconfirm title="确定删除?" @confirm="removeVariant(index)" :disabled="record.is_existing">
                              <Button danger type="text" size="small" :disabled="record.is_existing">
                                  {{ record.is_existing ? '锁定' : '删除' }}
                              </Button>
                          </Popconfirm>
                      </template>
                  </Table.Column>
              </Table>
              
              <Button type="dashed" block class="mt-2" @click="addVariant">
                  + 添加变体
              </Button>
          </div>
      </Card>
        
       <!-- Actions -->
       <div class="fixed bottom-0 left-0 right-0 p-4 bg-white border-t z-10 flex justify-end items-center gap-4 shadow-lg" style="width: 100%">
           <Button size="large" @click="resetForm">重置</Button>
           <Button type="primary" size="large" :loading="loading" @click="handleSave" style="min-width: 120px">创建产品</Button>
       </div>
       <div class="h-20"></div>

    </div>
  </Page>
</template>
