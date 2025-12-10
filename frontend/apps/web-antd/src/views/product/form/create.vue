<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { 
  Steps, 
  Card, 
  Form, 
  Select, 
  Cascader, 
  Input, 
  Button, 
  Space, 
  Divider, 
  message, 
  InputNumber 
} from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import { useRouter } from 'vue-router';
import { 
  getCategoriesApi, 
  previewProductCodesApi, 
  createProduct,
  getSkuSuffixesApi,
  getTaxCategories,
  getBrandsApi,
  getModelsApi,
  getYearsApi
} from '#/api/core/product';
import { getHSCodeList } from '#/api/serc/foundation';
import type { Category, Product, ProductVariant, Brand, Model, VehicleNode, SkuSuffix, TaxCategory } from '#/api/core/product';
import type { SysHSCode } from '#/api/serc/model';

const router = useRouter();
const currentStep = ref(0);
const loading = ref(false);

// --- Data Sources ---
const categories = ref<Category[]>([]);
const brands = ref<Brand[]>([]);
const models = ref<Model[]>([]);
const years = ref<VehicleNode[]>([]);
const skuSuffixes = ref<SkuSuffix[]>([]);
const hsCodes = ref<SysHSCode[]>([]);
const taxCategories = ref<TaxCategory[]>([]);

// --- Form State ---
const formState = reactive({
  // Step 1: Basic
  category_id: [] as string[], // Cascader array
  brand_id: undefined as string | undefined,
  model_id: undefined as string | undefined,
  year_id: undefined as string | undefined,
  name: '',
  spu_code: '', // Auto-generated or Manual
  
  // Step 2: Variants
  specs_config: [] as any[], // Selected spec options
  generated_variants: [] as any[], // Preview data
  
  // Compliance
  hs_code_id: undefined as number | undefined,
});

// --- Lifecycle ---
onMounted(async () => {
  try {
    const [cats, suffixRes, taxRes, hsRes, brandRes] = await Promise.all([
      getCategoriesApi(),
      getSkuSuffixesApi(),
      getTaxCategories(),
      getHSCodeList(),
      getBrandsApi()
    ]);
    categories.value = cats;
    // Suffixes might be wrapped
    skuSuffixes.value = Array.isArray(suffixRes) ? suffixRes : (suffixRes as any).data || [];
    taxCategories.value = Array.isArray(taxRes) ? taxRes : (taxRes as any).data || [];
    hsCodes.value = Array.isArray(hsRes) ? hsRes : (hsRes as any).data || [];
    brands.value = Array.isArray(brandRes) ? brandRes : (brandRes as any).data || [];
  } catch (e) {
    console.error(e);
  }
});

// --- Step 1 Handlers ---
async function handleCategoryChange(value: string[]) {
  // Reset vehicle selections if category changes (optional refinement)
}

async function handleBrandChange(val: string) {
  formState.model_id = undefined;
  formState.year_id = undefined;
  models.value = [];
  years.value = [];
  if (val) {
    const res = await getModelsApi(val);
    models.value = Array.isArray(res) ? res : (res as any).data || [];
  }
}

async function handleModelChange(val: string) {
  formState.year_id = undefined;
  years.value = [];
  if (val) {
    const res = await getYearsApi(val);
    years.value = Array.isArray(res) ? res : (res as any).data || [];
  }
}

// --- Step 2: Preview ---
async function handlePreview() {
  if (!formState.category_id || formState.category_id.length === 0) {
    message.error('请选择分类');
    return;
  }
  
  const lastCatId = formState.category_id[formState.category_id.length - 1];
  
  // Construct metadata for CodeBuilder
  const metadata: Record<string, any> = {};
  
  // Find selected vehicle names for metadata injection
  if (formState.brand_id) {
    const b = brands.value.find(x => String(x.id) === String(formState.brand_id));
    if (b) metadata['brand'] = b.abbr || b.code; // Use abbr for coding
  }
  if (formState.model_id) {
    const m = models.value.find(x => String(x.id) === String(formState.model_id));
    if (m) metadata['model'] = m.name; // Model usually uses name or mapped code, depends on CodeBuilder logic. Let's assume name for now or we need abbr in model.
    // NOTE: In backend Vehicle model, abbreviation is the key. 
    // We might need to fetch full object or assume frontend model list has abbr.
    // The getModelsApi returns Model interface which currently lacks abbr.
    // Let's assume name is safe for now, or backend lookup.
  }
  if (formState.year_id) {
    const y = years.value.find(x => String(x.id) === String(formState.year_id));
    if (y) metadata['year'] = y.name; // "07-13"
  }

  // Demo: single variant generation for now (complex matrix generation to be added)
  const demoVariant = {
     suffix: 'GEN', // Default
     specs: { color: 'Default' }
  };
  
  try {
    loading.value = true;
    const res = await previewProductCodesApi({
      category_id: Number(lastCatId),
      spu_coding_metadata: metadata,
      variants: [demoVariant] // TODO: Dynamic variants
    });
    
    // Bind results
    if (res) {
        formState.spu_code = res.spu_code;
        // Map variants
        formState.generated_variants = res.variants || [];
        currentStep.value = 1; // Go to next step
    }
  } catch (e) {
    // Error handled
  } finally {
    loading.value = false;
  }
}

// --- Step 3: Submit ---
async function handleSubmit() {
    try {
        loading.value = true;
        const lastCatId = formState.category_id[formState.category_id.length - 1];
        
        // Prepare Payload
        const payload = {
            category_id: Number(lastCatId),
            name: formState.name,
            spu_code: formState.spu_code, // Confirmed code
            brand_id: formState.brand_id, // Store ID relations
            // coding metadata is implicitly handled by create logic or passed explicitly?
            // Backend create_product expects "brand", "model", "year" strings for context if code not provided, 
            // but since we provided spu_code, we just need to ensure ProductVariant data is good.
            
            variants: formState.generated_variants.map(v => ({
                sku: v.sku, // Confirmed SKU
                feature_code: v.feature_code,
                specs: v.specs,
                price: 0, // TODO: input
                hs_code_id: formState.hs_code_id, // Inherit SPU level HS Code choice
            }))
        };
        
        await createProduct(payload);
        message.success('产品创建成功');
        router.push('/product/list');
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
}
</script>

<template>
  <Page title="创建新产品 (SPU)">
    <Card>
      <Steps :current="currentStep" class="mb-8 max-w-3xl mx-auto">
        <Steps.Step title="基础信息" description="定义产品身份" />
        <Steps.Step title="变体配置" description="生成 SKU" />
        <Steps.Step title="确认完成" />
      </Steps>

      <!-- Step 1: Basic Info -->
      <div v-show="currentStep === 0" class="max-w-2xl mx-auto">
        <Form layout="vertical" :model="formState">
          <Form.Item label="所属分类" required>
            <Cascader 
                v-model:value="formState.category_id"
                :options="categories" 
                :field-names="{ label: 'name', value: 'id', children: 'children' }"
                placeholder="请选择产品分类"
                @change="handleCategoryChange"
            />
          </Form.Item>
          
          <Form.Item label="产品名称" required>
             <Input v-model:value="formState.name" placeholder="请输入产品通用名称" />
          </Form.Item>

          <Divider orientation="left">车型/适配属性</Divider>
          <div class="grid grid-cols-3 gap-4">
             <Form.Item label="品牌 (Brand)">
                <Select 
                    v-model:value="formState.brand_id" 
                    :options="brands" 
                    :field-names="{ label: 'name', value: 'id' }"
                    @change="handleBrandChange"
                    show-search
                    option-filter-prop="name"
                />
             </Form.Item>
             <Form.Item label="车型 (Model)">
                <Select 
                    v-model:value="formState.model_id" 
                    :options="models" 
                    :field-names="{ label: 'name', value: 'id' }"
                    @change="handleModelChange"
                    :disabled="!formState.brand_id"
                />
             </Form.Item>
             <Form.Item label="年份 (Year)">
                <Select 
                    v-model:value="formState.year_id" 
                    :options="years" 
                    :field-names="{ label: 'name', value: 'id' }"
                    :disabled="!formState.model_id"
                />
             </Form.Item>
          </div>
          
          <Divider orientation="left">合规信息</Divider>
          <Form.Item label="HS 编码 (默认)">
             <Select 
                v-model:value="formState.hs_code_id"
                :options="hsCodes"
                :field-names="{ label: 'code', value: 'id' }"
                show-search
                option-filter-prop="code"
             >
                <template #option="{ code, name }">
                    <span>{{ code }}</span>
                    <span class="text-gray-400 ml-2 text-xs">{{ name }}</span>
                </template>
             </Select>
          </Form.Item>

          <div class="text-center mt-8">
             <Button type="primary" size="large" @click="handlePreview" :loading="loading">下一步：生成编码</Button>
          </div>
        </Form>
      </div>

      <!-- Step 2: Variants Preview -->
      <div v-show="currentStep === 1" class="max-w-4xl mx-auto">
         <div class="bg-gray-50 p-4 rounded mb-6 border border-gray-100">
            <div class="text-gray-500 text-sm">SPU 编码预览</div>
            <div class="text-2xl font-mono font-bold text-primary">{{ formState.spu_code }}</div>
         </div>
         
         <div class="mb-4 font-bold">生成的 SKU 列表</div>
         <!-- Simple list for now -->
         <div v-for="(v, idx) in formState.generated_variants" :key="idx" class="border p-3 rounded mb-2 flex justify-between items-center">
             <div>
                 <div class="font-mono font-bold">{{ v.sku }}</div>
                 <div class="text-xs text-gray-400">{{ v.feature_code }}</div>
             </div>
             <div>
                 <Tag color="blue">{{ v.suffix || 'GEN' }}</Tag>
             </div>
         </div>

         <div class="text-center mt-8">
             <Space>
                 <Button @click="currentStep = 0">上一步</Button>
                 <Button type="primary" size="large" @click="handleSubmit" :loading="loading">确认创建</Button>
             </Space>
          </div>
      </div>

    </Card>
  </Page>
</template>

