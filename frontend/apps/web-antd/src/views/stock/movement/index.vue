<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getStockMovementList, type StockMovement } from '#/api/stock';
import { Page } from '@vben/common-ui';

const gridOptions: VxeGridProps<StockMovement> = {
  columns: [
    { field: 'biz_time', title: '业务时间', width: 160, sortable: true },
    { field: 'order_no', title: '单据编号', width: 180 },
    { field: 'order_type', title: '类型', width: 100, slots: { default: 'type' } },
    { field: 'sku', title: 'SKU', width: 150 },
    { field: 'warehouse_id', title: '仓库ID', width: 80 },
    { 
      field: 'quantity_delta', 
      title: '变动数量', 
      width: 100, 
      slots: { default: 'delta' } 
    },
    { field: 'unit_cost', title: '单位成本', width: 100 },
    { field: 'currency', title: '币种', width: 80 },
    { field: 'status', title: '状态', width: 100 },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page, form }) => {
        return await getStockMovementList({
          page: page.currentPage,
          per_page: page.pageSize,
          ...form,
        });
      },
    },
  },
};

const [Grid] = useVbenVxeGrid({ 
  gridOptions,
});

const typeMap: Record<string, string> = {
  inbound: '入库',
  outbound: '出库',
  transfer: '调拨',
  adjustment: '调整',
};
</script>

<template>
  <Page title="库存流水">
    <Grid>
      <template #type="{ row }">
        {{ typeMap[row.order_type] || row.order_type }}
      </template>
      <template #delta="{ row }">
        <span :style="{ color: row.quantity_delta > 0 ? 'green' : 'red' }">
          {{ row.quantity_delta > 0 ? '+' : '' }}{{ row.quantity_delta }}
        </span>
      </template>
    </Grid>
  </Page>
</template>

