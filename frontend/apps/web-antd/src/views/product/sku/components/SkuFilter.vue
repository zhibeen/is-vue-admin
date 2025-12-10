<script setup lang="ts">
import { ref, watch, reactive } from 'vue';
import { 
  Form, 
  Input, 
  Select, 
  Button, 
  Row, 
  Col, 
  Card,
  Space,
  Tag
} from 'ant-design-vue';
import { SearchOutlined, FilterOutlined, CloseOutlined } from '@ant-design/icons-vue';

const emit = defineEmits<{
  (e: 'filter-change', filters: any): void;
  (e: 'search', value: string): void;
}>();

const expanded = ref(false);

// 使用reactive管理表单状态，避免Form.useForm()问题
const formState = reactive({
  q: '',
  category_id: undefined as number | undefined,
  brand: undefined as string | undefined,
  model: undefined as string | undefined,
  is_active: '' as string,
});

// 使用静态数据，避免API调用错误
const categories = [
  { id: 1, name: '前大灯' },
  { id: 2, name: '后尾灯' },
  { id: 3, name: '保险杠' },
  { id: 4, name: '后视镜' },
];

const brands = [
  { label: '大众', value: 'VW' },
  { label: '宝马', value: 'BMW' },
  { label: '奔驰', value: 'MB' },
  { label: '丰田', value: 'TOYOTA' },
  { label: '本田', value: 'HONDA' },
];

const models = [
  { label: '帕萨特', value: 'PASSAT' },
  { label: '迈腾', value: 'MAGOTAN' },
  { label: '3系', value: '3SERIES' },
  { label: '5系', value: '5SERIES' },
  { label: 'C级', value: 'C-CLASS' },
  { label: 'E级', value: 'E-CLASS' },
];

const statusOptions = [
  { label: '全部', value: '' },
  { label: '启用', value: 'true' },
  { label: '停用', value: 'false' },
];

// 处理筛选
function handleFilter() {
  // 构建筛选条件
  const filters: any = {};
  
  if (formState.category_id) {
    filters.category_id = formState.category_id;
  }
  
  if (formState.brand) {
    filters.brand = formState.brand;
  }
  
  if (formState.model) {
    filters.model = formState.model;
  }
  
  if (formState.is_active !== undefined && formState.is_active !== '') {
    filters.is_active = formState.is_active === 'true';
  }
  
  emit('filter-change', filters);
}

// 重置筛选
function handleReset() {
  formState.q = '';
  formState.category_id = undefined;
  formState.brand = undefined;
  formState.model = undefined;
  formState.is_active = '';
  emit('filter-change', {});
}

// 切换展开状态
function toggleExpanded() {
  expanded.value = !expanded.value;
}

// 活动筛选标签
const activeFilters = ref<any>({});

watch(() => ({ ...formState }), (values) => {
  const filters: any = {};
  
  if (values.category_id) {
    const category = categories.find(c => c.id === values.category_id);
    filters.category = category?.name;
  }
  
  if (values.brand) {
    const brand = brands.find(b => b.value === values.brand);
    filters.brand = brand?.label;
  }
  
  if (values.model) {
    const model = models.find(m => m.value === values.model);
    filters.model = model?.label;
  }
  
  if (values.is_active !== undefined && values.is_active !== '') {
    filters.status = values.is_active === 'true' ? '启用' : '停用';
  }
  
  activeFilters.value = filters;
}, { deep: true });

// 移除筛选标签
function removeFilter(key: string) {
  if (key === 'category') {
    formState.category_id = undefined;
  } else if (key === 'brand') {
    formState.brand = undefined;
  } else if (key === 'model') {
    formState.model = undefined;
  } else if (key === 'status') {
    formState.is_active = '';
  }
  handleFilter();
}

// 处理快速搜索
function handleQuickSearch() {
  emit('search', formState.q);
}
</script>

<template>
  <Card size="small">
    <template #title>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <FilterOutlined />
          <span>高级筛选</span>
          <Button type="link" size="small" @click="toggleExpanded">
            {{ expanded ? '收起' : '展开' }}
          </Button>
        </div>
        <div class="flex items-center gap-2">
          <Button size="small" @click="handleReset">
            <CloseOutlined /> 重置
          </Button>
          <Button type="primary" size="small" @click="handleFilter">
            <SearchOutlined /> 筛选
          </Button>
        </div>
      </div>
    </template>

    <!-- 筛选表单 -->
    <Form 
      layout="vertical" 
      class="filter-form"
      :class="{ 'expanded': expanded }"
    >
      <Row :gutter="[16, 16]">
        <Col :span="expanded ? 6 : 24">
          <Form.Item label="快速搜索" name="q">
            <Input 
              v-model:value="formState.q"
              placeholder="SKU编码、特征码、SPU编码、产品名称..." 
              @press-enter="handleQuickSearch"
            >
              <template #suffix>
                <SearchOutlined @click="handleQuickSearch" />
              </template>
            </Input>
          </Form.Item>
        </Col>
        
        <template v-if="expanded">
          <Col :span="6">
            <Form.Item label="产品分类" name="category_id">
              <Select 
                v-model:value="formState.category_id"
                placeholder="选择分类"
                :options="categories.map(c => ({ label: c.name, value: c.id }))"
                show-search
                option-filter-prop="label"
                allow-clear
              />
            </Form.Item>
          </Col>
          
          <Col :span="6">
            <Form.Item label="品牌" name="brand">
              <Select 
                v-model:value="formState.brand"
                placeholder="选择品牌"
                :options="brands"
                show-search
                option-filter-prop="label"
                allow-clear
              />
            </Form.Item>
          </Col>
          
          <Col :span="6">
            <Form.Item label="车型" name="model">
              <Select 
                v-model:value="formState.model"
                placeholder="选择车型"
                :options="models"
                show-search
                option-filter-prop="label"
                allow-clear
              />
            </Form.Item>
          </Col>
          
          <Col :span="6">
            <Form.Item label="状态" name="is_active">
              <Select 
                v-model:value="formState.is_active"
                placeholder="选择状态"
                :options="statusOptions"
                allow-clear
              />
            </Form.Item>
          </Col>
        </template>
      </Row>
    </Form>

    <!-- 活动筛选标签 -->
    <div v-if="Object.keys(activeFilters).length > 0" class="mt-4">
      <div class="text-sm text-gray-500 mb-2">当前筛选:</div>
      <Space wrap>
        <Tag 
          v-for="(value, key) in activeFilters" 
          :key="key"
          closable
          @close="removeFilter(key)"
        >
          {{ key === 'category' ? '分类' : 
             key === 'brand' ? '品牌' : 
             key === 'model' ? '车型' : 
             key === 'status' ? '状态' : key }}: {{ value }}
        </Tag>
      </Space>
    </div>
  </Card>
</template>

<style scoped>
.filter-form {
  transition: all 0.3s ease;
}

.filter-form.expanded {
  max-height: 500px;
  overflow: visible;
}
</style>
