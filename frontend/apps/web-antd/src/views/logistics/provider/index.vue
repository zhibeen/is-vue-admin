<script setup lang="ts">
/**
 * 物流服务商管理页面
 */
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { 
  getLogisticsProviders, 
  deleteLogisticsProvider,
  toggleLogisticsProviderStatus
} from '#/api/logistics/logistics-provider';
import { onMounted, ref } from 'vue';
import { Button, Tag, Space, message, Modal } from 'ant-design-vue';
import ProviderFormModal from './components/ProviderFormModal.vue';

// Grid配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 80 },
    { field: 'provider_code', title: '服务商编码', width: 130 },
    { field: 'provider_name', title: '服务商名称', minWidth: 180 },
    { 
      field: 'service_type', 
      title: '服务类型', 
      width: 130,
      slots: { default: 'service_type_default' }
    },
    { field: 'payment_method', title: '付款方式', width: 110 },
    { field: 'settlement_cycle', title: '结算周期', width: 110 },
    { field: 'contact_name', title: '联系人', width: 100 },
    { field: 'contact_phone', title: '联系电话', width: 140 },
    { 
      field: 'is_active', 
      title: '状态', 
      width: 90,
      slots: { default: 'is_active_default' }
    },
    { 
      title: '操作', 
      width: 200, 
      fixed: 'right',
      slots: { default: 'action_default' }
    },
  ],
  data: [],
  pagerConfig: { enabled: false },
  toolbarConfig: {
    refresh: true,
    refreshOptions: { code: 'query' },
    custom: true,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ 
  gridOptions,
  gridEvents: {
    toolbarToolClick: (params) => {
      if (params.code === 'query') loadData();
    }
  }
});

// 数据加载
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getLogisticsProviders();
    gridApi.setGridOptions({ data: res });
  } catch (e: any) {
    message.error('加载失败: ' + (e.message || '未知错误'));
  } finally {
    gridApi.setLoading(false);
  }
}

onMounted(() => {
  loadData();
});

// 新建/编辑
const showModal = ref(false);
const editingId = ref<number | null>(null);

function handleCreate() {
  editingId.value = null;
  showModal.value = true;
}

function handleEdit(row: any) {
  editingId.value = row.id;
  showModal.value = true;
}

function handleModalClose() {
  showModal.value = false;
  loadData();
}

// 删除
function handleDelete(row: any) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除服务商"${row.provider_name}"吗？`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteLogisticsProvider(row.id);
        message.success('删除成功');
        loadData();
      } catch (e: any) {
        message.error('删除失败: ' + (e.message || '未知错误'));
      }
    },
  });
}

// 切换启用状态
async function handleToggleStatus(row: any) {
  try {
    await toggleLogisticsProviderStatus(row.id);
    message.success('状态更新成功');
    loadData();
  } catch (e: any) {
    message.error('状态更新失败: ' + (e.message || '未知错误'));
  }
}

// 服务类型映射
function getServiceTypeText(type: string): string {
  const map: Record<string, string> = {
    domestic_trucking: '国内卡车运输',
    international_sea: '国际海运',
    international_air: '国际空运',
    customs_clearance: '清关服务',
    destination_delivery: '目的国派送',
  };
  return map[type] || type || '-';
}
</script>

<template>
  <div class="p-4">
    <Grid>
      <!-- 工具栏 -->
      <template #toolbar_buttons>
        <Button type="primary" @click="handleCreate">
          新建服务商
        </Button>
      </template>
      
      <!-- 服务类型列 -->
      <template #service_type_default="{ row }">
        {{ getServiceTypeText(row.service_type) }}
      </template>
      
      <!-- 状态列 -->
      <template #is_active_default="{ row }">
        <Tag :color="row.is_active ? 'green' : 'red'">
          {{ row.is_active ? '启用' : '停用' }}
        </Tag>
      </template>
      
      <!-- 操作列 -->
      <template #action_default="{ row }">
        <Space>
          <Button type="link" size="small" @click="handleEdit(row)">
            编辑
          </Button>
          <Button 
            type="link" 
            size="small" 
            @click="handleToggleStatus(row)"
          >
            {{ row.is_active ? '停用' : '启用' }}
          </Button>
          <Button 
            type="link" 
            danger 
            size="small" 
            @click="handleDelete(row)"
          >
            删除
          </Button>
        </Space>
      </template>
    </Grid>
    
    <!-- 表单弹窗 -->
    <ProviderFormModal 
      v-if="showModal"
      :visible="showModal"
      :provider-id="editingId"
      @close="handleModalClose"
    />
  </div>
</template>

