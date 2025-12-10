<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { 
  Card, 
  Table, 
  Select, 
  InputNumber, 
  Button, 
  Space, 
  Input,
  Tag,
  Alert,
  message,
  Popconfirm
} from 'ant-design-vue';
import { DeleteOutlined, CalculatorOutlined, SyncOutlined } from '@ant-design/icons-vue';
import { previewProductCodesApi } from '#/api/core/product';
import { useDebounceFn } from '@vueuse/core';

const props = defineProps<{
  categoryId?: number;
  spuMetadata?: any;
  value?: any[]; // variants
}>();

const emit = defineEmits(['update:value']);

// --- State ---
const showGenerator = ref(false);
const attributes = ref<any[]>([]); // Variant Attributes Config
const skuGenerationState = ref<Record<string, string[]>>({}); // Selected values for generation
const variants = ref<any[]>(props.value || []);
const isPreviewLoading = ref(false);

// --- Mock Attributes (Replace with API loadAttributes later) ---
// These should ideally come from backend: getCategoryAttributes(id, scope='sku')
const loadAttributes = async () => {
  if (!props.categoryId) return;
  // Mocking Variant Attributes for Demo
  attributes.value = [
    { key: 'color', label: '颜色 (Color)', options: ['Chrome', 'Black', 'Smoke', 'Clear', 'Red', 'Amber'], type: 'select' },
    { key: 'position', label: '位置 (Position)', options: ['Left', 'Right', 'Pair (Set)', 'Center'], type: 'select' },
    { key: 'material', label: '材质 (Material)', options: ['ABS', 'Steel', 'Aluminum'], type: 'select' }
  ];
};

// --- Helpers ---

// 1. Cartesian Product
const cartesian = (args: any[][]) => {
    if (args.length === 0) return [];
    return args.reduce((a, b) => {
        return a.flatMap(d => b.map(e => [d, e].flat()));
    }, [[]] as any[][]);
};

// 2. Suffix Calculator (Frontend Hint)
const calculateSuffixFromSpecs = (specs: Record<string, any>) => {
    const skuSuffixParts: string[] = [];
    const featureSuffixParts: string[] = [];
    
    // Order matters: use attributes order
    attributes.value.forEach(attr => {
        const val = specs[attr.key];
        if (!val) return;
        
        const strVal = String(val).toUpperCase();
        
        // --- Logic ported from reference create.vue ---
        
        // 1. System SKU Suffix (Simple Logic)
        let skuCode = '';
        if (attr.key === 'position' || attr.label.includes('位置')) {
            if (strVal.includes('PAIR') || strVal.includes('SET') || strVal.includes('对装')) {
                skuCode = ''; 
            } else if (strVal.includes('PASSENGER') || strVal.includes('RIGHT') || strVal.includes('右')) {
                skuCode = 'P'; 
            } else if (strVal.includes('DRIVER') || strVal.includes('LEFT') || strVal.includes('左')) {
                skuCode = 'D'; 
            } else {
                 skuCode = strVal.slice(0, 1);
            }
        } else {
            // Default: 1st char
            skuCode = strVal.slice(0, 1);
        }
        if (skuCode) skuSuffixParts.push(skuCode);
        
        // 2. Feature Code Suffix
        // Similar logic or specific mapping
        let featureCode = '';
        if (attr.key === 'position') {
             if (strVal.includes('PAIR') || strVal.includes('SET')) featureCode = '2P';
             else if (strVal.includes('RIGHT')) featureCode = 'P';
             else if (strVal.includes('LEFT')) featureCode = 'D';
             else featureCode = strVal.slice(0,1);
        } else {
            featureCode = strVal.slice(0, 3);
        }
        if (featureCode) featureSuffixParts.push(featureCode);
    });
    
    return {
        suffix: skuSuffixParts.join(''),
        feature_suffix: featureSuffixParts.length > 0 ? '-' + featureSuffixParts.join('-') : ''
    };
};

// --- Core Actions ---

// 3. Smart Merge Generator
const generateVariants = () => {
  const axes = attributes.value.map(attr => ({
      key: attr.key,
      label: attr.label,
      values: skuGenerationState.value[attr.key] || []
  })).filter(axis => axis.values.length > 0);

  if (axes.length === 0) {
      message.warning('请至少选择一个规格值');
      return;
  }

  const combos = axes.length === 1 
      ? axes[0].values.map(v => [v]) 
      : cartesian(axes.map(a => a.values));

  // Check existing
  const existingRows = variants.value.filter(v => v.id || v.is_existing); // Preserve backend saved rows
  const hasExisting = existingRows.length > 0;
  
  if (!hasExisting && variants.value.length > 0 && variants.value[0].sku) {
       // If frontend-only rows exist, confirm overwrite
       if (!confirm('重新生成将覆盖当前列表，是否继续？')) return;
  }

  const newVariants: any[] = [];
  let addedCount = 0;

  combos.forEach((combo: any[], idx) => {
      const flatCombo = Array.isArray(combo) ? combo : [combo];
      const specs: Record<string, any> = {};
      axes.forEach((axis, i) => {
           specs[axis.key] = flatCombo[i];
      });

      // --- SMART MERGE CHECK ---
      const match = existingRows.find(row => {
          if (!row.specs) return false;
          // Compare specs
          return Object.keys(specs).every(k => String(row.specs[k] || '') === String(specs[k] || ''));
      });

      if (match) {
          // Already exists in DB/Saved, skip adding new
          return;
      }
      
      // Create New
      const { suffix, feature_suffix } = calculateSuffixFromSpecs(specs);
      
      // Inherit default weights/dims from SPU Metadata if available
      // Note: spuMetadata might be reactive formState
      const defaultWeight = props.spuMetadata?.specs?.weight || props.spuMetadata?.weight || 0;

      newVariants.push({
          key: Date.now() + idx + Math.random(),
          sku: 'Pending...', 
          feature_code: 'Pending...',
          specs: specs,
          // price: 0, // Removed
          // cost_price: 0, // Removed
          weight: defaultWeight,
          net_weight: defaultWeight,
          pack_length: 0,
          pack_width: 0,
          pack_height: 0,
          
          // Temporary fields for UI
          _suffix: suffix,
          _feature_suffix: feature_suffix,
          name_suffix: flatCombo.join(' ')
      });
      addedCount++;
  });

  // Result: Existing + New
  variants.value = [...existingRows, ...newVariants];
  
  emit('update:value', variants.value);
  message.success(`生成完成：保留 ${existingRows.length} 个已有，新增 ${addedCount} 个`);
  
  // Trigger Preview
  previewCodes();
};

// 4. Preview Codes (Debounced)
const fetchPreviewData = async () => {
    if (!props.categoryId || variants.value.length === 0) return;
    
    try {
        isPreviewLoading.value = true;
        
        // Prepare Metadata: SPU Form State + Common Attributes
        const metadata = {
            ...props.spuMetadata,
            ...(props.spuMetadata?.attributes || {})
        };

        const res = await previewProductCodesApi({
            category_id: props.categoryId,
            spu_coding_metadata: metadata,
            variants: variants.value.map(v => ({
                ...(v.specs || {})
            }))
        });
        
        if (res && res.variants) {
            variants.value.forEach((v, idx) => {
                const pv = res.variants[idx];
                if (pv) {
                    v.sku = pv.sku;
                    v.feature_code = pv.feature_code;
                }
            });
        }
    } catch (e) {
        console.error("Preview Failed", e);
    } finally {
        isPreviewLoading.value = false;
    }
};

const previewCodes = useDebounceFn(fetchPreviewData, 500);

// --- Watchers ---

watch(() => props.categoryId, () => {
    loadAttributes();
    // variants.value = []; // Don't clear on category change automatically, let user decide or handle in parent
    skuGenerationState.value = {};
});

watch(() => props.value, (val) => {
    if (val) {
        variants.value = val;
    }
}, { deep: true });

// Watch metadata to re-trigger preview (e.g. if brand changes, SKU might change)
watch(() => props.spuMetadata, () => {
    if (variants.value.length > 0) {
        previewCodes();
    }
}, { deep: true });

// --- Columns ---
const columns = [
  { title: 'SKU (System)', dataIndex: 'sku', width: 150 },
  { title: 'Feature Code (Biz)', dataIndex: 'feature_code', width: 180 },
  { title: '规格 (Specs)', dataIndex: 'specs', width: 220 },
  { title: '重量 (毛/净 KG)', dataIndex: 'weight', width: 140 },
  { title: '包装尺寸 (L/W/H CM)', dataIndex: 'pack_dims', width: 200 },
  { title: '操作', key: 'action', width: 60, align: 'center' }
];

function removeVariant(index: number) {
  variants.value.splice(index, 1);
  emit('update:value', variants.value);
}
</script>

<template>
  <div class="variant-manager">
    
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-2">
            <span class="text-base font-bold text-gray-700">SKU 变体列表</span>
            <Tag color="blue">{{ variants.length }} Variants</Tag>
        </div>
        <Space>
            <Button @click="showGenerator = !showGenerator" :type="showGenerator ? 'default' : 'primary'" ghost>
                <template #icon><CalculatorOutlined /></template>
                {{ showGenerator ? '收起生成器' : '变体生成器' }}
            </Button>
        </Space>
    </div>

    <!-- Generator Panel -->
    <div v-if="showGenerator" class="bg-orange-50 p-4 mb-4 rounded border border-orange-200 border-dashed transition-all">
        <Alert 
           v-if="!categoryId"
           message="请先在上访选择商品分类以加载规格配置" 
           type="warning" 
           show-icon 
           class="mb-4"
        />
        <div v-else>
           <div class="mb-3 text-gray-500 text-xs">选择规格值进行组合（笛卡尔积），系统将自动合并新增项。</div>
           <div class="grid grid-cols-3 gap-4 mb-4">
               <div v-for="attr in attributes" :key="attr.key" class="bg-white p-2 rounded border border-orange-100">
                  <div class="mb-1 text-xs text-gray-700 font-bold">{{ attr.label }}</div>
                  <Select
                     v-model:value="skuGenerationState[attr.key]"
                     mode="multiple"
                     style="width: 100%"
                     placeholder="点击选择..."
                     :options="attr.options.map((o: any) => ({ label: o, value: o }))"
                     :max-tag-count="2"
                  />
               </div>
           </div>
           
           <div class="flex justify-end border-t border-orange-200 pt-3">
               <Button type="primary" @click="generateVariants">
                  <SyncOutlined /> 生成 / 增量合并
               </Button>
           </div>
        </div>
    </div>

    <!-- Table -->
    <Table 
        :dataSource="variants" 
        :columns="columns" 
        size="small"
        :pagination="false"
        rowKey="key"
        bordered
        :scroll="{ x: 1000 }"
    >
        <template #bodyCell="{ column, record, index }">
            
            <!-- SKU Preview -->
            <template v-if="column.dataIndex === 'sku'">
                 <div class="flex flex-col">
                     <div class="flex items-center gap-1">
                         <span v-if="isPreviewLoading" class="text-gray-300 text-xs">...</span>
                         <span v-else class="font-mono font-bold text-blue-700">{{ record.sku || 'Pending' }}</span>
                     </div>
                 </div>
            </template>
            
            <!-- Feature Code Preview -->
            <template v-if="column.dataIndex === 'feature_code'">
                 <div class="flex items-center gap-1">
                     <span v-if="isPreviewLoading" class="text-gray-300 text-xs">...</span>
                     <Tag v-else color="cyan" class="font-mono text-xs">{{ record.feature_code || '-' }}</Tag>
                 </div>
            </template>

            <!-- Specs Tags -->
            <template v-else-if="column.dataIndex === 'specs'">
                <div class="flex flex-wrap gap-1">
                    <Tag v-for="(val, key) in record.specs" :key="key" class="mr-0 mb-1" color="orange">
                        {{ key }}: {{ val }}
                    </Tag>
                </div>
                <div class="mt-1">
                    <Input 
                        v-model:value="record.name_suffix" 
                        size="small" 
                        placeholder="名称后缀 (如: 左侧)" 
                        class="text-xs"
                    />
                </div>
            </template>
            
            <!-- Prices Removed -->
            
            <!-- Weights -->
            <template v-else-if="column.dataIndex === 'weight'">
                <Space :size="2" direction="vertical" style="width: 100%">
                    <InputNumber v-model:value="record.weight" placeholder="毛重" :min="0" :precision="3" size="small" style="width: 100%">
                        <template #addonAfter>G</template>
                    </InputNumber>
                    <InputNumber v-model:value="record.net_weight" placeholder="净重" :min="0" :precision="3" size="small" style="width: 100%">
                        <template #addonAfter>N</template>
                    </InputNumber>
                </Space>
            </template>

            <!-- Dimensions -->
            <template v-else-if="column.dataIndex === 'pack_dims'">
                <Input.Group compact>
                    <InputNumber v-model:value="record.pack_length" placeholder="L" :min="0" size="small" style="width: 33%" />
                    <InputNumber v-model:value="record.pack_width" placeholder="W" :min="0" size="small" style="width: 33%" />
                    <InputNumber v-model:value="record.pack_height" placeholder="H" :min="0" size="small" style="width: 34%" />
                </Input.Group>
            </template>
            
            <!-- Actions -->
            <template v-else-if="column.key === 'action'">
                <Popconfirm title="确定删除该变体?" @confirm="removeVariant(index)">
                    <Button type="text" danger size="small">
                        <DeleteOutlined />
                    </Button>
                </Popconfirm>
            </template>
        </template>
    </Table>
  </div>
</template>

<style scoped>
/* Optional: specific styles if needed */
</style>