<template>
  <div class="p-4">
    <!-- 工具栏 -->
    <Card class="mb-4">
      <Space>
        <Button @click="handleRefresh">
          <template #icon><ReloadOutlined /></template>
          刷新
        </Button>
      </Space>
    </Card>

    <!-- 列表 -->
    <Card>
      <Grid ref="gridRef" />
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  Card,
  Button,
  Space,
  message,
} from 'ant-design-vue';
import { ReloadOutlined, EyeOutlined } from '@ant-design/icons-vue';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { requestClient } from '#/api/request';

// 交付合同接口类型（临时定义）
interface DeliveryContract {
  id: number;
  contract_no: string;
  shipment_id?: number;
  supplier_id: number;
  company_id?: number;
  total_amount: number;
  currency: string;
  status: string;
  has_supply_contract: boolean;
  delivery_date?: string;
  created_at: string;
}

// Grid配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 80 },
    { field: 'contract_no', title: '合同号', width: 150 },
    { field: 'shipment_id', title: '发货单ID', width: 100 },
    { field: 'supplier_id', title: '供应商ID', width: 100 },
    { field: 'total_amount', title: '总金额', width: 120 },
    { field: 'currency', title: '币种', width: 80 },
    { field: 'status', title: '状态', width: 100 },
    { field: 'has_supply_contract', title: '已生成开票合同', width: 140,
      slots: { default: ({ row }: { row: DeliveryContract }) => row.has_supply_contract ? '是' : '否' }
    },
    { field: 'delivery_date', title: '交付日期', width: 120 },
    { field: 'created_at', title: '创建时间', width: 160 },
    {
      title: '操作',
      width: 100,
      fixed: 'right',
      slots: {
        default: ({ row }: { row: DeliveryContract }) => [
          {
            type: 'button',
            text: '查看',
            icon: EyeOutlined,
            onClick: () => handleView(row),
          },
        ],
      },
    },
  ],
  data: [],
  pagerConfig: {
    enabled: true,
  },
};

// 初始化Grid
const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions,
});

// 加载数据
async function loadData() {
  try {
    gridApi.setLoading(true);
    // 使用现有的交付合同API（假设在 /api/v1/supply/contracts）
    const res = await requestClient.get<{ items: DeliveryContract[] }>(
      '/v1/supply/contracts',
      { params: { page: 1, per_page: 100 } }
    );
    gridApi.setGridOptions({ data: res.items || [] });
  } catch (error) {
    console.error('加载交付合同列表失败:', error);
    message.error('加载数据失败');
  } finally {
    gridApi.setLoading(false);
  }
}

// 查看
function handleView(row: DeliveryContract) {
  message.info(`查看交付合同: ${row.contract_no}`);
  // TODO: 跳转到详情页或打开详情弹窗
}

// 刷新
function handleRefresh() {
  loadData();
}

// 挂载时加载数据
onMounted(() => {
  loadData();
});
</script>

<style scoped>
/* 样式可以根据需要添加 */
</style>

