<template>
  <div class="p-4">
    <PageWrapper title="SKU分组管理" content="管理SKU分组，用于库存分配策略的中间层颗粒度">
      <div class="mb-4">
        <a-space>
          <a-button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新建分组
          </a-button>
          <a-button @click="handleRefresh">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </div>

      <div class="mb-4">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索分组编码或名称"
          style="width: 300px"
          @search="handleSearch"
        />
      </div>

      <div class="bg-white">
        <VbenVxeGrid ref="gridRef" :grid-options="gridOptions" />
      </div>
    </PageWrapper>

    <!-- 创建/编辑分组弹窗 -->
    <ProductGroupModal
      v-model:visible="modalVisible"
      :record="currentRecord"
      :mode="modalMode"
      @success="handleModalSuccess"
    />

    <!-- SKU管理弹窗 -->
    <SkuManagementModal
      v-model:visible="skuModalVisible"
      :group-id="currentGroupId"
      @success="handleSkuModalSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { PageWrapper } from '@vben/layouts';
import { VbenVxeGrid } from '#/adapter/vxe-table';
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined, AppstoreOutlined } from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import ProductGroupModal from '../components/ProductGroupModal.vue';
import SkuManagementModal from '../components/SkuManagementModal.vue';
import { getProductGroupList, deleteProductGroup, type ProductGroup } from '#/api/virtual';
import type { VxeGridProps, VxeGridInstance } from '#/adapter/vxe-table';

const gridRef = ref<VxeGridInstance>();
const searchKeyword = ref('');
const modalVisible = ref(false);
const skuModalVisible = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const currentRecord = ref<ProductGroup | null>(null);
const currentGroupId = ref<number>(0);

// 表格配置
const gridOptions = reactive<VxeGridProps>({
  border: true,
  stripe: true,
  showOverflow: true,
  keepSource: true,
  height: 'auto',
  columns: [
    { type: 'seq', width: 60, title: '序号' },
    { field: 'code', title: '分组编码', width: 120 },
    { field: 'name', title: '分组名称', width: 150 },
    { field: 'note', title: '备注', minWidth: 200 },
    { field: 'created_at', title: '创建时间', width: 180 },
    {
      title: '操作',
      width: 250,
      fixed: 'right',
      slots: {
        default: ({ row }: { row: ProductGroup }) => {
          return (
            <div class="flex gap-2">
              <a-button
                type="link"
                size="small"
                onClick={() => handleManageSkus(row.id)}
              >
                <AppstoreOutlined /> 管理SKU
              </a-button>
              <a-button
                type="link"
                size="small"
                onClick={() => handleEdit(row)}
              >
                <EditOutlined /> 编辑
              </a-button>
              <a-button
                type="link"
                size="small"
                danger
                onClick={() => handleDelete(row)}
              >
                <DeleteOutlined /> 删除
              </a-button>
            </div>
          );
        }
      }
    }
  ],
  data: [],
  pagerConfig: {
    enabled: true,
    pageSize: 20,
    pageSizes: [10, 20, 50, 100],
    layouts: ['PrevJump', 'PrevPage', 'Number', 'NextPage', 'NextJump', 'Sizes', 'Total']
  },
  toolbarConfig: {
    refresh: true,
    refreshOptions: { code: 'query' },
    custom: true
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const params = {
            page: page.currentPage,
            per_page: page.pageSize,
            q: searchKeyword.value || undefined
          };
          const res = await getProductGroupList(params);
          return {
            result: res.items,
            page: { total: res.total }
          };
        } catch (error) {
          console.error('获取SKU分组列表失败:', error);
          message.error('获取SKU分组列表失败');
          return { result: [], page: { total: 0 } };
        }
      }
    }
  }
});

// 加载数据
const loadData = () => {
  gridRef.value?.commitProxy('query');
};

// 搜索
const handleSearch = () => {
  loadData();
};

// 刷新
const handleRefresh = () => {
  searchKeyword.value = '';
  loadData();
};

// 创建分组
const handleCreate = () => {
  currentRecord.value = null;
  modalMode.value = 'create';
  modalVisible.value = true;
};

// 编辑分组
const handleEdit = (record: ProductGroup) => {
  currentRecord.value = record;
  modalMode.value = 'edit';
  modalVisible.value = true;
};

// 管理SKU
const handleManageSkus = (groupId: number) => {
  currentGroupId.value = groupId;
  skuModalVisible.value = true;
};

// 删除分组
const handleDelete = (record: ProductGroup) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除SKU分组 "${record.name}" 吗？此操作不可恢复。`,
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteProductGroup(record.id);
        message.success('删除成功');
        loadData();
      } catch (error) {
        console.error('删除失败:', error);
        message.error('删除失败');
      }
    }
  });
};

// 弹窗成功回调
const handleModalSuccess = () => {
  modalVisible.value = false;
  loadData();
};

// SKU管理弹窗成功回调
const handleSkuModalSuccess = () => {
  skuModalVisible.value = false;
  // 可以在这里刷新分组信息
};

onMounted(() => {
  loadData();
});
</script>
