<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getHSCodeList } from '#/api/serc/foundation';
import { onMounted } from 'vue';

const gridOptions: VxeGridProps = {
  columns: [
    { field: 'code', title: 'HS编码', width: 150, fixed: 'left' },
    { field: 'name', title: '商品名称', minWidth: 200 },
    { field: 'refund_rate', title: '退税率', width: 100, formatter: ({ cellValue }) => `${(cellValue * 100).toFixed(0)}%` },
  ],
  proxyConfig: {
    ajax: {
      query: async () => {
        const res = await getHSCodeList();
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
    refresh: true,
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
