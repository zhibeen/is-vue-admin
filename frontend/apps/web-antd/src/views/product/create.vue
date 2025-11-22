<script lang="ts" setup>
import { ref, watch, computed, onMounted } from 'vue';
import { Card, Form, Select, Input, InputNumber, Switch, Row, Col, Button, Space, message, Cascader } from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import type { Category, Brand, SkuSuffix, CategoryAttribute, Model } from '#/api/core/product';
import { getCategoriesApi, getBrandsApi, getSkuSuffixesApi, getCategoryAttributesApi, getModelsApi, getNextSkuSerialApi } from '#/api/core/product';

const formState = ref({
  category: [] as string[], // Cascader value array
  brandId: undefined as string | undefined,
  modelId: undefined as string | undefined,
  skuSuffix: undefined as string | undefined,
  name: '',
  specs: {
      length: 0,
      width: 0,
      height: 0,
      weight: 0
  },
  dynamicAttrs: {} as Record<string, any>,
  mockSerial: null as string | null
});

// --- Data Sources ---
const categories = ref<Category[]>([]);
const brands = ref<Brand[]>([]);
const models = ref<Model[]>([]);
const skuSuffixes = ref<SkuSuffix[]>([]);
const dynamicAttrDefinitions = ref<CategoryAttribute[]>([]);

// --- Computed Helpers ---
const currentCategoryCode = computed(() => {
    if (!formState.value.category || formState.value.category.length === 0) return '';
    // Simple logic to find leaf node code - recursively or flat map in real app
    // Here we assume 2 levels for demo
    const leafId = formState.value.category[formState.value.category.length - 1];
    // In a real app, we'd traverse the tree to find the code. 
    // For this mock, we'll cheat a bit or need a helper to find node by ID.
    // Let's implement a simple recursive finder
    const findNode = (nodes: Category[], id: string): Category | null => {
        for (const node of nodes) {
            if (node.id === id) return node;
            if (node.children) {
                const found = findNode(node.children, id);
                if (found) return found;
            }
        }
        return null;
    };
    const node = findNode(categories.value, leafId);
    return node ? node.code : '';
});

const currentBrandCode = computed(() => {
    const brand = brands.value.find(b => b.id === formState.value.brandId);
    return brand ? brand.code : '';
});

const skuPreview = computed(() => {
    const catCode = currentCategoryCode.value || '???';
    const brandCode = currentBrandCode.value || '??';
    const suffix = formState.value.skuSuffix || '';
    
    const prefix = `${catCode}${brandCode}`;
    const serial = formState.value.mockSerial || '####';
    
    return {
        text: `${prefix}${serial}${suffix}`,
        isCalculated: !!formState.value.mockSerial
    };
});

// Watch for prefix changes to update mock serial
watch([currentCategoryCode, currentBrandCode], async ([newCat, newBrand]) => {
    formState.value.mockSerial = null;
    if (newCat && newBrand) {
        const prefix = `${newCat}${newBrand}`;
        try {
            // Debounce could be added here in real app
            const serial = await getNextSkuSerialApi(prefix);
            formState.value.mockSerial = serial;
        } catch (e) {
            console.error('Failed to fetch mock serial');
        }
    }
});

// --- Lifecycle & Watchers ---
onMounted(async () => {
    try {
        const [cats, brs, sufs] = await Promise.all([
            getCategoriesApi(),
            getBrandsApi(),
            getSkuSuffixesApi()
        ]);
        categories.value = cats;
        brands.value = brs;
        skuSuffixes.value = sufs;
    } catch (e) {
        message.error('Failed to load initial data');
    }
});

// Watch brand change to load models
watch(() => formState.value.brandId, async (newVal) => {
    formState.value.modelId = undefined;
    models.value = [];
    if (newVal) {
        try {
            models.value = await getModelsApi(newVal);
        } catch (e) {
             message.error('Failed to load models');
        }
    }
});
watch(() => formState.value.category, async (newVal) => {
    // Reset dynamic attributes
    formState.value.dynamicAttrs = {};
    dynamicAttrDefinitions.value = [];

    if (newVal && newVal.length > 0) {
        const leafId = newVal[newVal.length - 1];
        try {
            const attrs = await getCategoryAttributesApi(leafId);
            dynamicAttrDefinitions.value = attrs;
            
            // Initialize default values for booleans or others if needed
            attrs.forEach(attr => {
                if(attr.type === 'boolean') {
                    formState.value.dynamicAttrs[attr.key] = false;
                }
            });

        } catch (e) {
            message.error('Failed to load attributes');
        }
    }
});

const handleSave = () => {
    console.log('Submitting:', formState.value);
    message.success('Save logic not implemented yet');
};

</script>

<template>
  <Page title="创建新产品">
    <div class="max-w-5xl mx-auto space-y-4">
      
      <!-- 1. Core Classification (The Driver) -->
      <Card title="1. 分类与SKU" :bordered="false">
        <Form layout="vertical">
          <Row :gutter="16">
            <Col :span="12">
              <Form.Item label="产品分类" required tooltip="决定可用的规格属性">
                <Cascader 
                    v-model:value="formState.category" 
                    :options="categories" 
                    :field-names="{ label: 'name', value: 'id', children: 'children' }"
                    placeholder="请选择分类" 
                />
              </Form.Item>
            </Col>
            <Col :span="8">
              <Form.Item label="汽车品牌 (Make)" required>
                <Select 
                    v-model:value="formState.brandId" 
                    :options="brands" 
                    :field-names="{ label: 'name', value: 'id' }"
                    placeholder="请选择品牌" 
                />
              </Form.Item>
            </Col>
             <Col :span="8">
              <Form.Item label="车型 (Model)" required>
                <Select 
                    v-model:value="formState.modelId" 
                    :options="models" 
                    :field-names="{ label: 'name', value: 'id' }"
                    placeholder="请选择车型"
                    :disabled="!formState.brandId"
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Row :gutter="16">
             <Col :span="12">
               <Form.Item label="SKU 后缀 (变体)" tooltip="可选的变体标识符">
                 <Select 
                    v-model:value="formState.skuSuffix"
                    allowClear
                    placeholder="选择后缀 (如 左侧, 右侧)"
                 >
                    <Select.Option v-for="s in skuSuffixes" :key="s.code" :value="s.code">
                        {{ s.code }} - {{ s.meaning }}
                    </Select.Option>
                 </Select>
               </Form.Item>
             </Col>
             <Col :span="12">
                <Form.Item label="SKU 预览 (试算结果)">
                    <div class="text-2xl font-mono font-bold text-black bg-yellow-300 p-2 rounded border border-dashed border-yellow-500 text-center relative">
                        {{ skuPreview.text }}
                        <span v-if="skuPreview.isCalculated" class="absolute top-0 right-0 text-xs bg-green-500 text-white px-1 rounded-bl">
                            预生成
                        </span>
                    </div>
                    <div class="text-xs text-gray-400 mt-1 text-center">
                        * 实际流水号将在保存时最终确认
                    </div>
                </Form.Item>
             </Col>
          </Row>
        </Form>
      </Card>

      <!-- 2. Dynamic Attributes -->
      <Card title="2. 规格参数" :bordered="false" v-if="dynamicAttrDefinitions.length > 0">
          <Form layout="vertical">
              <Row :gutter="16">
                  <Col :span="8" v-for="attr in dynamicAttrDefinitions" :key="attr.id">
                      <Form.Item :label="attr.label" :required="attr.required">
                          
                          <!-- Select Type -->
                          <Select v-if="attr.type === 'select'" 
                                  v-model:value="formState.dynamicAttrs[attr.key]"
                                  placeholder="请选择">
                              <Select.Option v-for="opt in attr.options" :key="opt.value" :value="opt.value">
                                  {{ opt.label }}
                              </Select.Option>
                          </Select>

                          <!-- Boolean Type -->
                          <Switch v-else-if="attr.type === 'boolean'" 
                                  v-model:checked="formState.dynamicAttrs[attr.key]" />

                          <!-- Number Type -->
                          <InputNumber v-else-if="attr.type === 'number'"
                                       v-model:value="formState.dynamicAttrs[attr.key]"
                                       class="w-full" />

                          <!-- Default Text -->
                          <Input v-else 
                                 v-model:value="formState.dynamicAttrs[attr.key]" />
                      </Form.Item>
                  </Col>
              </Row>
          </Form>
      </Card>

       <!-- 3. Basic Info -->
       <Card title="3. 基础信息" :bordered="false">
           <Form layout="vertical">
               <Form.Item label="产品名称" required>
                   <Input v-model:value="formState.name" placeholder="官方产品名称" />
               </Form.Item>
               
               <div class="grid grid-cols-4 gap-4">
                   <Form.Item label="长 (cm)">
                       <InputNumber v-model:value="formState.specs.length" />
                   </Form.Item>
                   <Form.Item label="宽 (cm)">
                       <InputNumber v-model:value="formState.specs.width" />
                   </Form.Item>
                   <Form.Item label="高 (cm)">
                       <InputNumber v-model:value="formState.specs.height" />
                   </Form.Item>
                   <Form.Item label="重量 (kg)">
                       <InputNumber v-model:value="formState.specs.weight" />
                   </Form.Item>
               </div>
           </Form>
       </Card>
        
       <!-- Actions -->
       <div class="fixed bottom-0 left-0 right-0 p-4 bg-white border-t z-10 flex justify-end gap-4 shadow-lg" style="width: 100%">
           <Button>重置</Button>
           <Button type="primary" size="large" @click="handleSave">创建产品</Button>
       </div>
       <!-- Add padding to bottom to prevent footer overlap -->
       <div class="h-20"></div>

    </div>
  </Page>
</template>

<style scoped>
.text-primary {
    color: var(--primary-color);
}
</style>

