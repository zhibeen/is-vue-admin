<template>
  <div class="p-4">
    <PageWrapper title="虚拟仓列表" content="管理所有虚拟仓，包括销售虚拟仓和采购虚拟仓">
      <div class="mb-4">
        <a-space>
          <a-button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新建虚拟仓
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
          placeholder="搜索虚拟仓编码或名称"
          style="width: 300px"
          @search="handleSearch"
        />
      </div>

      <div class="bg-white">
        <VbenVxeGrid ref="gridRef" :grid-options="gridOptions" />
      </div>
    </PageWrapper>

    <!-- 创建/编辑虚拟仓弹窗 -->
    <VirtualWarehouseModal
      v-model:visible="modalVisible"
      :record="currentRecord"
      :mode="modalMode"
      @success="handleModalSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { PageWrapper } from '@vben/layouts';
import { VbenVxeGrid } from '#/adapter/vxe-table';
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import { useRouter } from 'vue-router';
import VirtualWarehouseModal from '../components/VirtualWarehouseModal.vue';
import { getVirtualWarehouseList, deleteVirtualWarehouse } from '#/api/virtual';
import type { VirtualWarehouse } from '#/api/virtual';
import type { VxeGridProps, VxeGridInstance } from '#/adapter/vxe-table';

const router = useRouter();
const gridRef = ref<VxeGridInstance>();
const searchKeyword = ref('');
const modalVisible = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const currentRecord = ref<VirtualWarehouse | null>(null);

// 表格配置
const gridOptions = reactive<VxeGridProps>({
  border: true,
  stripe: true,
  showOverflow: true,
  keepSource: true,
  height: 'auto',
  columns: [
    { type: 'seq', width: 60, title: '序号' },
    { field: 'code', title: '虚拟仓编码', width: 120 },
    { field: 'name', title: '虚拟仓名称', width: 150 },
    { 
      field: 'category', 
      title: '形态', 
      width: 100,
      formatter: ({ cellValue }) => {
        const map = { physical: '实体仓', virtual: '虚拟仓' };
        return map[cellValue as keyof typeof map] || cellValue;
      }
    },
    { 
      field: 'location_type', 
      title: '地理位置', 
      width: 100,
      formatter: ({ cellValue }) => {
        const map = { domestic: '国内', overseas: '海外' };
        return map[cellValue as keyof typeof map] || cellValue;
      }
    },
    { 
      field: 'status', 
      title: '状态', 
      width: 100,
      formatter: ({ cellValue }) => {
        const map = {
          planning: '筹备中',
          active: '正常',
          suspended: '暂停',
          clearing: '清退中',
          deprecated: '已废弃'
        };
        return map[cellValue as keyof typeof map] || cellValue;
      }
    },
    { 
      field: 'business_type', 
      title: '业务类型', 
      width: 120,
      formatter: ({ cellValue }) => {
        const map = {
          standard: '标准仓',
          fba: 'FBA仓',
          bonded: '保税仓',
          transit: '中转仓'
        };
        return map[cellValue as keyof typeof map] || cellValue;
      }
    },
    { field: 'currency', title: '计价币种', width: 100 },
    { field: 'created_at', title: '创建时间', width: 180 },
    {
      title: '操作',
      width: 200,
      fixed: 'right',
      slots: {
        default: ({ row }: { row: VirtualWarehouse }) => {
          return (
            <div class="flex gap-2">
              <a-button
                type="link"
                size="small"
                onClick={() => handleViewDetail(row.id)}
              >
                <EyeOutlined /> 详情
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
    refresh: { code: 'query' },
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
          const res = await getVirtualWarehouseList(params);
          return {
            result: res.items,
            page: { total: res.total }
          };
        } catch (error) {
          console.error('获取虚拟仓列表失败:', error);
          message.error('获取虚拟仓列表失败');
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

// 查看详情
const handleViewDetail = (id: number) => {
  router.push(`/wms/virtual/detail/${id}`);
};

// 创建虚拟仓
const handleCreate = () => {
  currentRecord.value = null;
  modalMode.value = 'create';
  modalVisible.value = true;
};

// 编辑虚拟仓
const handleEdit = (record: VirtualWarehouse) => {
  currentRecord.value = record;
  modalMode.value = 'edit';
  modalVisible.value = true;
};

// 删除虚拟仓
const handleDelete = (record: VirtualWarehouse) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除虚拟仓 "${record.name}" 吗？此操作不可恢复。`,
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteVirtualWarehouse(record.id);
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

onMounted(() => {
  loadData();
});
</script>
