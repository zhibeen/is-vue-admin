<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getStockList, type Stock } from '#/api/stock';
import { Page } from '@vben/common-ui';

const gridOptions: VxeGridProps<Stock> = {
  columns: [
    { field: 'sku', title: 'SKU', width: 150, fixed: 'left', sortable: true },
    { field: 'warehouse_id', title: '仓库ID', width: 100 },
    { field: 'batch_no', title: '批次号', width: 120 },
    { field: 'physical_quantity', title: '物理库存', width: 100, sortable: true },
    { field: 'available_quantity', title: '可用库存', width: 100, sortable: true },
    { field: 'allocated_quantity', title: '已分配', width: 100 },
    { field: 'in_transit_quantity', title: '在途', width: 100 },
    { field: 'damaged_quantity', title: '坏品', width: 100 },
    { field: 'updated_at', title: '更新时间', width: 160 },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page, form }) => {
        return await getStockList({
          page: page.currentPage,
          per_page: page.pageSize,
          ...form,
        });
      },
    },
  },
  toolbarConfig: {
    custom: true,
    export: true,
    refresh: true,
  },
};

const [Grid] = useVbenVxeGrid({ 
  gridOptions,
});
</script>

<template>
  <Page title="库存总览">
    <Grid />
  </Page>
</template>

