<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';

// Mock Data for now
const mockData = [
  { id: 1, currency: 'USD', rate: 7.2, safe_min: 5.5, safe_max: 8.0, is_active: true, updated_at: '2023-11-25' },
];

const gridOptions: VxeGridProps = {
  columns: [
    { field: 'currency', title: '币种', width: 100 },
    { field: 'rate', title: '基准汇率', width: 120 },
    { field: 'safe_min', title: '安全下限', width: 120 },
    { field: 'safe_max', title: '安全上限', width: 120 },
    { field: 'is_active', title: '启用', width: 100, formatter: 'formatBoolean' },
    { field: 'updated_at', title: '更新时间', minWidth: 150 },
  ],
  data: mockData,
  toolbarConfig: {
    refresh: true,
    zoom: true,
  },
};

const [Grid] = useVbenVxeGrid({ gridOptions });
</script>

<template>
  <div class="p-4">
    <Grid />
  </div>
</template>

