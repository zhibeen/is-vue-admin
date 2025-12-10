<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { 
  Spin, 
  message, 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  Button, 
  Card, 
  Alert,
  Divider, 
  Row, 
  Col, 
  Space,
  Cascader,
  Table,
  Tag,
  Tabs // Added Tabs
} from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import { 
  createProduct, 
  getProduct, 
  updateProduct,
  type Product,
  type ProductVariant
} from '#/api/core/product';
import { getCategoriesApi, previewProductCodesApi } from '#/api/core/product';
import VehicleCascader from './components/VehicleCascader.vue';
import VariantGenerator from './components/VariantGenerator.vue';
import AttributeForm from './components/AttributeForm.vue';
import { DeleteOutlined, SyncOutlined, CalculatorOutlined, EditOutlined, PlusOutlined, UploadOutlined, FileTextOutlined, GlobalOutlined, SearchOutlined } from '@ant-design/icons-vue';

const route = useRoute();
const router = useRouter();

const id = computed(() => route.params.id as string);
const isEdit = computed(() => !!id.value);
const isView = ref(!!route.params.id); 
const loading = ref(false);
const submitting = ref(false);

const activeTab = ref('autoparts');

// --- Form State ---
const formRef = ref();
const formState = reactive<any>({
  category_id: null,
  spu_code: '', // Optional override
  name: '',
  brand: 'JZB', // Default or from config
  model: '',
  year: '',
  
  // Attributes (Dynamic)
  attributes: {},
  
  // Variants (SKUs)
  variants: []
});

// --- Options ---
const categoryOptions = ref([]);

// --- Methods ---

function toggleEdit() {
  isView.value = false;
}

function handleCancel() {
  if (isEdit.value) {
    isView.value = true;
    loadData(); // Revert
  } else {
    router.back();
  }
}

function handleVehicleChange(val: any[], selectedOptions: any[]) {
  // Assuming 3 levels: [Make, Model, Year]
  if (selectedOptions.length > 0) {
      // 1. Store path
      formState.vehicle_path = val;
      
      // 2. Extract Metadata for SPU Coding
      selectedOptions.forEach((node) => {
          if (node.level_type) {
              // Store as top-level keys for easy access or in a metadata object
              // Backend expects: make_code, model_code, year
              if (node.level_type === 'make') {
                  formState.make_code = node.code;
                  formState.brand = node.name; // Auto-fill brand name
              }
              if (node.level_type === 'model') {
                  formState.model_code = node.code;
                  formState.model = node.name;
              }
              if (node.level_type === 'year') {
                  formState.year = node.name; // or node.code
              }
          }
      });
  }
}

// Helper: Find path in tree by leaf ID
function findCategoryPath(tree: any[], targetId: number, path: number[] = []): number[] | null {
  for (const node of tree) {
    if (node.id === targetId) {
      return [...path, node.id];
    }
    if (node.children) {
      const res = findCategoryPath(node.children, targetId, [...path, node.id]);
      if (res) return res;
    }
  }
  return null;
}

async function loadData() {
  loading.value = true;
  try {
    // Load Categories
    const cats = await getCategoriesApi();
    categoryOptions.value = cats; 
    
    if (isEdit.value) {
      // Default to View Mode when entering Edit page
      isView.value = true;
      
      const product = await getProduct(Number(id.value));
      Object.assign(formState, product);

      // Fix Category Path for Cascader
      if (product.category_id) {
          const path = findCategoryPath(cats, product.category_id);
          if (path) {
              formState.category_id = path; // Set full path array
          }
      }
      
      // Ensure variants are loaded into formState for the generator
      if (product.variants && product.variants.length > 0) {
          formState.variants = product.variants.map((v: any) => ({
              ...v,
              // Flatten specs if needed, or ensure format matches generator expectation
              // Generator expects: { sku, specs: {...}, price, ... }
              // Backend returns specs as Dict, so it should match directly.
          }));
      }
    }
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function handleSubmit() {
  try {
    await formRef.value?.validate();
    submitting.value = true;
    
    if (isEdit.value) {
      // Handle Cascader Array -> Single ID
      const catId = Array.isArray(formState.category_id) 
          ? formState.category_id[formState.category_id.length - 1] 
          : formState.category_id;

      await updateProduct(Number(id.value), {
          ...formState,
          category_id: catId
      });
      message.success('更新成功');
      isView.value = true;
    } else {
      const catId = Array.isArray(formState.category_id) 
          ? formState.category_id[formState.category_id.length - 1] 
          : formState.category_id;

      await createProduct({
          ...formState,
          category_id: catId
      });
      message.success('创建成功');
      router.push('/product/spu');
    }
  } catch (e) {
    console.error(e);
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <Page :title="isEdit ? '编辑产品' : '新建产品'" auto-content-height>
    <div class="p-4 pb-20">
      <Form
        ref="formRef"
        :model="formState"
        layout="vertical"
        :disabled="isView"
      >
        <!-- 1. 基础信息 -->
        <Card title="基础信息 (Basic Info)" class="mb-4" :bordered="false">
           <Row :gutter="24">
             <Col :span="8">
               <Form.Item label="商品分类" name="category_id" :rules="[{ required: true }]">
                 <Cascader 
                   v-model:value="formState.category_id" 
                   :options="categoryOptions" 
                   :field-names="{ label: 'name', value: 'id', children: 'children' }"
                   placeholder="请选择分类"
                 />
               </Form.Item>
             </Col>
             <Col :span="8">
               <Form.Item label="品牌" name="brand">
                 <Input v-model:value="formState.brand" />
               </Form.Item>
             </Col>
             <Col :span="8">
               <Form.Item label="核心车型 (Core Vehicle)" name="vehicle_path" help="用于生成 SPU 编码的核心车型参数">
                 <VehicleCascader 
                    v-model:value="formState.vehicle_path"
                    @change="handleVehicleChange"
                 />
               </Form.Item>
             </Col>
             <Col :span="24">
               <Form.Item label="商品名称 (SPU Name)" name="name" :rules="[{ required: true }]">
                 <Input v-model:value="formState.name" size="large" />
               </Form.Item>
             </Col>
           </Row>
        </Card>

        <!-- 2. 公共属性 -->
        <Card title="公共属性 (Common Attributes)" class="mb-4" :bordered="false" v-if="formState.category_id">
           <AttributeForm 
              :category-id="Array.isArray(formState.category_id) ? formState.category_id[formState.category_id.length - 1] : formState.category_id"
              v-model:value="formState.attributes"
           />
        </Card>

        <!-- 3. 变体管理 (SKU Variants) - Always visible -->
        <Card title="变体管理 (SKU Variants)" class="mb-4" :bordered="false" :body-style="{ padding: '12px 24px' }">
           <VariantGenerator
              :category-id="Array.isArray(formState.category_id) ? formState.category_id[formState.category_id.length - 1] : formState.category_id"
              :spu-metadata="formState"
              v-model:value="formState.variants"
           />
        </Card>

        <!-- 4. 适配车型 (Fitment) - Tabs -->
        <Card title="适配车型 (Fitment)" class="mb-4" :bordered="false">
            <Tabs v-model:activeKey="activeTab">
                <Tabs.TabPane key="autoparts" tab="AutoParts (US)">
                    <div class="mb-4">
                        <Space>
                            <Button type="primary">
                                <template #icon><PlusOutlined /></template>
                                手工添加
                            </Button>
                            <Button>
                                <template #icon><UploadOutlined /></template>
                                导入表格 (CSV/Excel)
                            </Button>
                            <Button>
                                <template #icon><FileTextOutlined /></template>
                                粘贴文本解析
                            </Button>
                            <Button>
                                <template #icon><GlobalOutlined /></template>
                                解析 eBay 兼容性
                            </Button>
                        </Space>
                    </div>
                    
                    <!-- Table Placeholder -->
                    <div class="p-8 text-center text-gray-400 border-2 border-dashed border-gray-200 rounded">
                        <p class="mb-2">AutoParts (ACES) Fitment Data List</p>
                        <p class="text-xs">支持 Make / Model / Year / Engine / Notes 批量导入</p>
                    </div>
                </Tabs.TabPane>
                
                <Tabs.TabPane key="tecdoc" tab="TecDoc (EU)">
                    <div class="mb-4">
                        <Space>
                            <Button type="primary">
                                <template #icon><PlusOutlined /></template>
                                手工添加 (K-Type)
                            </Button>
                            <Button>
                                <template #icon><UploadOutlined /></template>
                                导入表格
                            </Button>
                            <Button>
                                <template #icon><SearchOutlined /></template>
                                检索 TecDoc 数据库
                            </Button>
                        </Space>
                    </div>

                    <div class="p-8 text-center text-gray-400 border-2 border-dashed border-gray-200 rounded">
                        <p class="mb-2">TecDoc (K-Type) Fitment Data List</p>
                        <p class="text-xs">支持 K-Type / N-Type 关联与查询</p>
                    </div>
                </Tabs.TabPane>
            </Tabs>
        </Card>
      </Form>

      <div class="fixed-footer-actions">
           <Space>
             <template v-if="isView">
               <Button @click="router.back()">返回</Button>
               <Button type="primary" @click="toggleEdit">
                 <EditOutlined /> 编辑
               </Button>
             </template>
             <template v-else>
               <Button @click="handleCancel">取消</Button>
               <Button type="primary" :loading="submitting" @click="handleSubmit">保存</Button>
             </template>
           </Space>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.fixed-footer-actions {
  position: fixed;
  bottom: 0;
  right: 0;
  width: 100%;
  background: #fff;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  text-align: right;
  z-index: 999;
}
</style>
