<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Modal, message, Button, Space, Card, Tree, type TreeProps } from 'ant-design-vue';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import { 
  deleteWarehouse, 
  getWarehouseStats, 
  type WarehouseQuery, 
  type Warehouse, 
  type WarehouseStats as IWarehouseStats
} from '#/api/warehouse';

// 组件导入
import WarehouseStats from './components/WarehouseStats.vue';
import SearchFilter from './components/SearchFilter.vue';
import WarehouseTable from './components/WarehouseTable.vue';
import WarehouseModal from './components/WarehouseModal.vue';

const router = useRouter();
const tableRef = ref<InstanceType<typeof WarehouseTable>>();

// 搜索表单状态
const searchParams = reactive<WarehouseQuery>({
  keyword: '',
  category: undefined,
  location_type: undefined,
  ownership_type: undefined,
  status: undefined,
});

// 监听searchParams变化
watch(() => ({ ...searchParams }), (newValue, oldValue) => {
  console.log('index.vue searchParams changed:', {
    old: oldValue,
    new: newValue
  });
}, { deep: true });

// 编辑弹窗状态
const modalVisible = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const currentRecord = ref<Warehouse | null>(null);


// 树相关状态
const selectedKeys = ref<string[]>(['all']);

const treeData: TreeProps['treeData'] = [
  {
    title: '全部仓库',
    key: 'all',
    children: [
      {
        title: '按形态',
        key: 'category_group',
        selectable: false,
        children: [
          { title: '实体仓', key: 'category:physical' },
          { title: '虚拟仓', key: 'category:virtual' },
        ],
      },
      {
        title: '按位置',
        key: 'location_group',
        selectable: false,
        children: [
          { title: '国内', key: 'location_type:domestic' },
          { title: '海外', key: 'location_type:overseas' },
        ],
      },
      {
        title: '按性质',
        key: 'ownership_group',
        selectable: false,
        children: [
          { title: '自营', key: 'ownership_type:self' },
          { title: '三方', key: 'ownership_type:third_party' },
        ],
      },
    ],
  },
];

// 默认展开的节点
const expandedKeys = ref<string[]>(['all', 'category_group', 'location_group', 'ownership_group']);

// 处理树节点选择
function handleTreeSelect(keys: any[]) {
  if (keys.length === 0) {
    // 如果取消选中，默认切回 'all'
    selectedKeys.value = ['all'];
    // 递归调用处理逻辑
    handleTreeSelect(['all']);
    return;
  }
  
  const key = keys[0] as string;
  // if (!key) return; // 上面已经处理了空的情况

  // 重置分类相关的筛选参数，保留关键词
  searchParams.category = undefined;
  searchParams.location_type = undefined;
  searchParams.ownership_type = undefined;
  searchParams.status = undefined; // 切换大类时也可以重置状态

  if (key === 'all') {
    handleSearch();
    return;
  }

  // 解析 key: "field:value"
  const [field, value] = key.split(':');
  if (field && value) {
    (searchParams as any)[field] = value;
  }
  
  // 触发搜索
  handleSearch();
}

// 统计信息
const stats = ref<IWarehouseStats>({
  total: 0,
  physical: 0,
  virtual: 0,
  domestic: 0,
  overseas: 0,
  active: 0,
});

// 加载统计信息
const loadStats = async () => {
  try {
    const data = await getWarehouseStats();
    stats.value = data;
  } catch (error) {
    console.error('Failed to load warehouse stats:', error);
  }
};

onMounted(() => {
  loadStats();
});

// 更新搜索参数（处理 v-model 更新）
function handleUpdateSearchParams(value: WarehouseQuery) {
  console.log('=== index.vue handleUpdateSearchParams ===');
  console.log('收到 update:modelValue 事件，新值:', value);
  console.log('更新前 searchParams:', JSON.parse(JSON.stringify(searchParams)));
  
  Object.assign(searchParams, value);
  
  console.log('更新后 searchParams:', JSON.parse(JSON.stringify(searchParams)));
  console.log('=== handleUpdateSearchParams 结束 ===');
}

// 搜索处理
function handleSearch() {
  console.log('=== index.vue handleSearch ===');
  console.log('收到 search 事件，当前 searchParams:', JSON.parse(JSON.stringify(searchParams)));
  console.log('准备调用 tableRef.reload()');
  tableRef.value?.reload();
  loadStats();
  console.log('=== index.vue handleSearch 结束 ===');
}

// 重置搜索
function handleReset() {
  console.log('index.vue handleReset called');
  // 重置树选择
  selectedKeys.value = ['all'];
  
  Object.assign(searchParams, {
    keyword: '',
    category: undefined,
    location_type: undefined,
    ownership_type: undefined,
    status: undefined,
  });
  tableRef.value?.reload();
  loadStats();
}

// 操作处理
function handleViewDetail(row: Warehouse) {
  router.push(`/wms/settings/warehouse/detail/${row.id}`);
}

function handleEdit(row: Warehouse) {
  currentRecord.value = row;
  modalMode.value = 'edit';
  modalVisible.value = true;
}

function handleDelete(row: Warehouse) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除仓库 "${row.name}" 吗？如果仓库有库存将无法删除。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteWarehouse(row.id);
        message.success('删除成功');
        tableRef.value?.reload();
        loadStats();
      } catch (error) {
        // 错误通常由 request 拦截器处理
      }
    },
  });
}

// 创建新仓库
function handleCreate() {
  currentRecord.value = null;
  modalMode.value = 'create';
  modalVisible.value = true;
}

// 弹窗成功回调
function handleModalSuccess() {
  modalVisible.value = false;
  tableRef.value?.reload();
  loadStats();
}
</script>

<template>
  <div class="warehouse-list-page">
    <!-- 页面标题和操作区域 -->
    <div class="mb-6">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">仓库管理</h1>
          <p class="text-gray-500 mt-1">管理所有仓库，包括实体仓、虚拟仓、国内仓、海外仓等</p>
        </div>
        <Space>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新建仓库
          </Button>
          <Button @click="() => { tableRef?.reload(); loadStats(); }">
            <template #icon><ReloadOutlined /></template>
            刷新
          </Button>
        </Space>
      </div>

      <!-- 统计卡片 -->
      <WarehouseStats :stats="stats" />
    </div>

    <!-- 搜索筛选区域 -->
    <div class="flex gap-4">
      <!-- 左侧分类树 -->
      <div class="w-64 flex-shrink-0">
        <Card :bordered="false" class="h-full" :body-style="{ padding: '12px' }">
          <Tree
            v-model:selectedKeys="selectedKeys"
            v-model:expandedKeys="expandedKeys"
            :tree-data="treeData"
            block-node
            @select="handleTreeSelect"
          />
        </Card>
      </div>

      <!-- 右侧内容区域 -->
      <div class="flex-1 min-w-0">
        <SearchFilter
          :model-value="searchParams"
          @update:model-value="handleUpdateSearchParams"
          @search="handleSearch"
          @reset="handleReset"
        />

        <!-- 数据表格 -->
        <WarehouseTable
          ref="tableRef"
          :search-params="searchParams"
          @view-detail="handleViewDetail"
          @edit="handleEdit"
          @delete="handleDelete"
        />
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <WarehouseModal
      v-model:visible="modalVisible"
      :record="currentRecord"
      :mode="modalMode"
      @success="handleModalSuccess"
    />
  </div>
</template>

<style scoped>
.warehouse-list-page {
  padding: 16px;
}

:deep(.ant-card) {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
}

:deep(.ant-card-head) {
  border-bottom: none;
}
</style>
