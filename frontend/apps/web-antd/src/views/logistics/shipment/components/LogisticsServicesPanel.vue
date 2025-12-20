<script setup lang="ts">
/**
 * 发货单详情 - 物流服务Tab
 * 展示物流服务明细列表，支持添加、编辑、删除、确认
 */
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { 
  getShipmentLogisticsServices, 
  deleteShipmentLogisticsService,
  confirmShipmentLogisticsService,
  getShipmentLogisticsTotalCost
} from '#/api/logistics/shipment-logistics-service';
import { onMounted, ref, computed } from 'vue';
import { Button, Tag, Space, Statistic, message, Modal } from 'ant-design-vue';
import LogisticsServiceFormModal from './LogisticsServiceFormModal.vue';

const props = defineProps<{
  shipmentId: number;
}>();

// 物流总成本
const totalCost = ref(0);

// Grid配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 60 },
    { field: 'logistics_provider_name', title: '物流服务商', minWidth: 150 },
    { 
      field: 'service_type', 
      title: '服务类型', 
      width: 130,
      slots: { default: 'service_type_default' }
    },
    { field: 'service_description', title: '服务描述', minWidth: 200 },
    { 
      field: 'estimated_amount', 
      title: '预估费用', 
      width: 110,
      slots: { default: 'amount_default' }
    },
    { 
      field: 'actual_amount', 
      title: '实际费用', 
      width: 110,
      slots: { default: 'amount_default' }
    },
    { field: 'payment_method', title: '付款方式', width: 100 },
    { 
      field: 'status', 
      title: '状态', 
      width: 90,
      slots: { default: 'status_default' }
    },
    { 
      title: '操作', 
      width: 150, 
      fixed: 'right',
      slots: { default: 'action_default' }
    },
  ],
  data: [],
  toolbarConfig: {
    refresh: true,
    refreshOptions: { code: 'query' },
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

// 加载数据
async function loadData() {
  try {
    gridApi.setLoading(true);
    const [services, costData] = await Promise.all([
      getShipmentLogisticsServices(props.shipmentId),
      getShipmentLogisticsTotalCost(props.shipmentId)
    ]);
    gridApi.setGridOptions({ data: services });
    totalCost.value = costData.total_logistics_cost;
  } catch (e: any) {
    message.error('加载物流服务失败');
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

function handleAdd() {
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
    content: `确定要删除"${row.logistics_provider_name}"的服务吗？`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteShipmentLogisticsService(props.shipmentId, row.id);
        message.success('删除成功');
        loadData();
      } catch (e: any) {
        message.error('删除失败: ' + (e.message || '未知错误'));
      }
    },
  });
}

// 确认服务
async function handleConfirm(row: any) {
  try {
    await confirmShipmentLogisticsService(props.shipmentId, row.id);
    message.success('确认成功');
    loadData();
  } catch (e: any) {
    message.error('确认失败: ' + (e.message || '未知错误'));
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

// 状态颜色映射
function getStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    pending: 'default',
    confirmed: 'blue',
    reconciled: 'orange',
    paid: 'green',
  };
  return colorMap[status] || 'default';
}

// 状态文本映射
function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    pending: '待确认',
    confirmed: '已确认',
    reconciled: '已对账',
    paid: '已付款',
  };
  return textMap[status] || status;
}

// 格式化金额
function formatAmount(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) {
    return '-';
  }
  return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
</script>

<template>
  <div>
    <!-- 工具栏 -->
    <div class="mb-4 flex justify-between items-center">
      <Button type="primary" @click="handleAdd">
        添加物流服务
      </Button>
      <Statistic 
        title="物流总费用" 
        :value="totalCost" 
        :precision="2" 
        prefix="¥"
        class="text-right"
        :value-style="{ color: '#cf1322', fontSize: '20px', fontWeight: 'bold' }"
      />
    </div>
    
    <!-- 表格 -->
    <Grid>
      <!-- 服务类型列 -->
      <template #service_type_default="{ row }">
        {{ getServiceTypeText(row.service_type) }}
      </template>
      
      <!-- 金额列 -->
      <template #amount_default="{ row, column }">
        {{ formatAmount(row[column.field]) }}
      </template>
      
      <!-- 状态列 -->
      <template #status_default="{ row }">
        <Tag :color="getStatusColor(row.status)">
          {{ getStatusText(row.status) }}
        </Tag>
      </template>
      
      <!-- 操作列 -->
      <template #action_default="{ row }">
        <Space>
          <Button 
            v-if="row.status === 'pending'"
            type="link" 
            size="small" 
            @click="handleConfirm(row)"
          >
            确认
          </Button>
          <Button type="link" size="small" @click="handleEdit(row)">
            编辑
          </Button>
          <Button 
            v-if="row.status === 'pending' || row.status === 'confirmed'"
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
    <LogisticsServiceFormModal 
      v-if="showModal"
      :visible="showModal"
      :shipment-id="shipmentId"
      :service-id="editingId"
      @close="handleModalClose"
    />
  </div>
</template>

