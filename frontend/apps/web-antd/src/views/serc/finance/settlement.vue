<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getSOAList } from '#/api/serc/finance';
import { onMounted } from 'vue';

const gridOptions: VxeGridProps = {
  columns: [
    { field: 'soa_no', title: '结算单号', minWidth: 180 },
    { field: 'supplier_name', title: '供应商', minWidth: 150 },
    { field: 'total_payable', title: '应付总额', minWidth: 120, formatter: 'formatMoney' },
    { field: 'paid_amount', title: '已付金额', minWidth: 120, formatter: 'formatMoney' },
    { field: 'payment_status', title: '资金状态', width: 100 },
    { field: 'invoice_status', title: '票据状态', width: 100 },
    { field: 'created_at', title: '创建日期', width: 150 },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        const res = await getSOAList({
          page: page.currentPage,
          per_page: page.pageSize,
        });
        return {
          result: res,
          total: res.length, 
        };
      },
    },
  },
  pagerConfig: {
    enabled: false,
  },
  toolbarConfig: {
    custom: true,
    export: true,
    refresh: true,
    resizable: true,
    search: true,
    zoom: true,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

onMounted(() => {
  gridApi.query();
});
</script>

<template>
  <div class="p-4">
    <Grid />
  </div>
</template>
