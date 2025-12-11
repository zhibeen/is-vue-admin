<template>
  <Card class="mb-4" :bordered="false">
    <div class="mb-4">
      <Space>
        <Input
          v-model:value="searchForm.keyword"
          placeholder="搜索仓库编码或名称"
          style="width: 300px"
          @press-enter="handleSearch"
        >
          <template #suffix>
            <SearchOutlined />
          </template>
        </Input>
        <Button type="primary" @click="handleSearch">
          <template #icon><SearchOutlined /></template>
          搜索
        </Button>
        <Button @click="handleReset">重置</Button>
        <Button @click="toggleAdvancedFilter">
          <template #icon><FilterOutlined /></template>
          {{ showAdvancedFilter ? '收起筛选' : '高级筛选' }}
        </Button>
      </Space>
    </div>

    <!-- 高级筛选面板 -->
    <div v-if="showAdvancedFilter" class="advanced-filter-panel">
      <Divider orientation="left" class="text-sm">高级筛选</Divider>
      <Row :gutter="16">
        <Col :span="6">
          <Form.Item label="仓库形态">
            <Select
              v-model:value="searchForm.category"
              placeholder="全部形态"
              allow-clear
              mode="multiple"
              style="width: 100%"
            >
              <Select.Option value="physical">实体仓</Select.Option>
              <Select.Option value="virtual">虚拟仓</Select.Option>
            </Select>
          </Form.Item>
        </Col>
        <Col :span="6">
          <Form.Item label="地理位置">
            <Select
              v-model:value="searchForm.location_type"
              placeholder="全部位置"
              allow-clear
              mode="multiple"
              style="width: 100%"
            >
              <Select.Option value="domestic">国内</Select.Option>
              <Select.Option value="overseas">海外</Select.Option>
            </Select>
          </Form.Item>
        </Col>
        <Col :span="6">
          <Form.Item label="管理模式">
            <Select
              v-model:value="searchForm.ownership_type"
              placeholder="全部模式"
              allow-clear
              mode="multiple"
              style="width: 100%"
            >
              <Select.Option value="self">自营</Select.Option>
              <Select.Option value="third_party">第三方</Select.Option>
            </Select>
          </Form.Item>
        </Col>
        <Col :span="6">
          <Form.Item label="状态">
            <Select
              v-model:value="searchForm.status"
              placeholder="全部状态"
              allow-clear
              mode="multiple"
              style="width: 100%"
            >
              <Select.Option value="planning">筹备中</Select.Option>
              <Select.Option value="active">正常</Select.Option>
              <Select.Option value="suspended">暂停</Select.Option>
              <Select.Option value="clearing">清退中</Select.Option>
              <Select.Option value="deprecated">已废弃</Select.Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>
      <div class="text-right">
        <Space>
          <Button @click="handleReset">重置筛选</Button>
          <Button type="primary" @click="handleSearch">应用筛选</Button>
        </Space>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { 
  Card, Input, Select, Space, Button, Form, Divider, Row, Col 
} from 'ant-design-vue';
import { 
  SearchOutlined, FilterOutlined 
} from '@ant-design/icons-vue';
import type { WarehouseQuery } from '#/api/warehouse';

interface Props {
  modelValue: WarehouseQuery;
}

interface Emits {
  (e: 'update:modelValue', value: WarehouseQuery): void;
  (e: 'search'): void;
  (e: 'reset'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const showAdvancedFilter = ref(false);

// 本地搜索表单状态
const searchForm = reactive<{
  keyword: string;
  category: string[];
  location_type: string[];
  ownership_type: string[];
  status: string[];
}>({
  keyword: props.modelValue.keyword || '',
  category: props.modelValue.category 
    ? (Array.isArray(props.modelValue.category) 
        ? props.modelValue.category 
        : (typeof props.modelValue.category === 'string' ? props.modelValue.category.split(',') : [props.modelValue.category]))
    : [],
  location_type: props.modelValue.location_type
    ? (Array.isArray(props.modelValue.location_type)
        ? props.modelValue.location_type
        : (typeof props.modelValue.location_type === 'string' ? props.modelValue.location_type.split(',') : [props.modelValue.location_type]))
    : [],
  ownership_type: props.modelValue.ownership_type
    ? (Array.isArray(props.modelValue.ownership_type)
        ? props.modelValue.ownership_type
        : (typeof props.modelValue.ownership_type === 'string' ? props.modelValue.ownership_type.split(',') : [props.modelValue.ownership_type]))
    : [],
  status: props.modelValue.status
    ? (Array.isArray(props.modelValue.status)
        ? props.modelValue.status
        : (typeof props.modelValue.status === 'string' ? props.modelValue.status.split(',') : [props.modelValue.status]))
    : [],
});

// 搜索处理
function handleSearch() {
  console.log('SearchFilter handleSearch called, searchForm:', JSON.parse(JSON.stringify(searchForm)));
  
  // 将数组转换为逗号分隔的字符串（空数组转换为undefined）
  const formattedData = {
    keyword: searchForm.keyword || '',
    category: searchForm.category.length > 0 ? searchForm.category.join(',') : undefined,
    location_type: searchForm.location_type.length > 0 ? searchForm.location_type.join(',') : undefined,
    ownership_type: searchForm.ownership_type.length > 0 ? searchForm.ownership_type.join(',') : undefined,
    status: searchForm.status.length > 0 ? searchForm.status.join(',') : undefined,
  };
  
  console.log('格式化后的数据:', formattedData);
  emit('update:modelValue', formattedData);
  emit('search');
}

// 重置搜索
function handleReset() {
  console.log('SearchFilter handleReset called');
  Object.assign(searchForm, {
    keyword: '',
    category: [],
    location_type: [],
    ownership_type: [],
    status: [],
  });
  
  emit('update:modelValue', { 
    keyword: '',
    category: undefined,
    location_type: undefined,
    ownership_type: undefined,
    status: undefined,
  });
  emit('reset');
}

// 切换高级筛选
function toggleAdvancedFilter() {
  showAdvancedFilter.value = !showAdvancedFilter.value;
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  console.log('SearchFilter: props.modelValue changed:', newValue);
  Object.assign(searchForm, {
    keyword: newValue.keyword || '',
    category: newValue.category
      ? (Array.isArray(newValue.category)
          ? newValue.category
          : (typeof newValue.category === 'string' ? newValue.category.split(',') : [newValue.category]))
      : [],
    location_type: newValue.location_type
      ? (Array.isArray(newValue.location_type)
          ? newValue.location_type
          : (typeof newValue.location_type === 'string' ? newValue.location_type.split(',') : [newValue.location_type]))
      : [],
    ownership_type: newValue.ownership_type
      ? (Array.isArray(newValue.ownership_type)
          ? newValue.ownership_type
          : (typeof newValue.ownership_type === 'string' ? newValue.ownership_type.split(',') : [newValue.ownership_type]))
      : [],
    status: newValue.status
      ? (Array.isArray(newValue.status)
          ? newValue.status
          : (typeof newValue.status === 'string' ? newValue.status.split(',') : [newValue.status]))
      : [],
  });
}, { deep: true });
</script>

<style scoped>
.advanced-filter-panel {
  background: #fafafa;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}
</style>
