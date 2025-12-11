<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getPolicyList, deletePolicy, type AllocationPolicy } from '#/api/virtual';
import { getWarehouseList, type Warehouse } from '#/api/warehouse';
import { Page } from '@vben/common-ui';
import { Button, message, Select, Modal, Tag } from 'ant-design-vue';
import { ref, onMounted, watch } from 'vue';

const currentVirtualWarehouseId = ref<number | undefined>(undefined);
const virtualWarehouses = ref<Warehouse[]>([]);

// 加载虚拟仓列表
async function loadVirtualWarehouses() {
  const res = await getWarehouseList({ category: 'virtual', per_page: 100 });
  virtualWarehouses.value = res.items;
  if (res.items.length > 0) {
    currentVirtualWarehouseId.value = res.items[0].id;
  }
}

const gridOptions: VxeGridProps<AllocationPolicy> = {
  columns: [
    { field: 'priority', title: '优先级', width: 80, sortable: true },
    { field: 'sku', title: 'SKU', width: 150 },
    { field: 'warehouse_product_group_id', title: 'SKU组ID', width: 100 },
    { field: 'category_id', title: '分类ID', width: 100 },
    { field: 'source_warehouse_id', title: '源仓ID', width: 100 },
    { 
      field: 'ratio', 
      title: '分配比例', 
      width: 100,
      formatter: ({ cellValue }) => cellValue ? `${cellValue * 100}%` : '-' 
    },
    { field: 'fixed_amount', title: '固定量', width: 100 },
    { field: 'policy_mode', title: '模式', width: 100, slots: { default: 'mode' } },
    { title: '操作', width: 150, fixed: 'right', slots: { default: 'action' } },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        if (!currentVirtualWarehouseId.value) return { items: [], total: 0 };
        return await getPolicyList(currentVirtualWarehouseId.value, {
          page: page.currentPage,
          per_page: page.pageSize,
        });
      },
    },
  },
  toolbarConfig: {
    custom: true,
    refresh: true,
    slots: { buttons: 'toolbar_buttons' }
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

watch(currentVirtualWarehouseId, () => {
  gridApi.reload();
});

function handleAdd() {
  message.info('新增策略功能开发中...');
}

function handleDelete(row: AllocationPolicy) {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这条策略吗？',
    onOk: async () => {
      await deletePolicy(row.id);
      message.success('删除成功');
      gridApi.reload();
    }
  });
}

onMounted(() => {
  loadVirtualWarehouses();
});
</script>

<template>
  <Page title="分配策略配置">
    <div class="mb-4 flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded">
      <span class="font-bold">选择虚拟仓:</span>
      <Select
        v-model:value="currentVirtualWarehouseId"
        style="width: 250px"
        placeholder="请选择虚拟仓"
        :options="virtualWarehouses.map(w => ({ label: w.name, value: w.id }))"
      />
    </div>

    <Grid>
      <template #toolbar_buttons>
        <Button type="primary" @click="handleAdd">新增策略</Button>
      </template>
      <template #mode="{ row }">
        <Tag :color="row.policy_mode === 'override' ? 'red' : 'blue'">
          {{ row.policy_mode === 'override' ? '覆盖' : '继承' }}
        </Tag>
      </template>
      <template #action="{ row }">
        <Button type="link" size="small">编辑</Button>
        <Button type="link" size="small" danger @click="handleDelete(row)">删除</Button>
      </template>
    </Grid>
  </Page>
</template>

