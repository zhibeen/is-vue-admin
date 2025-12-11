<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { onMounted, ref } from 'vue';
import { Button as AButton, Space, Tag, Input, Select } from 'ant-design-vue';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import { getStockList, type Stock } from '#/api/warehouse/stock';
import { getWarehouseList, type Warehouse } from '#/api/warehouse/index';

// --- State ---
const warehouseOptions = ref<{ label: string; value: number }[]>([]);
const searchSku = ref('');
const searchWarehouseId = ref<number | undefined>(undefined);

// --- Grid Config ---
const gridOptions: VxeGridProps = {
  keepSource: true,
  height: 'auto',
  autoResize: true,
  pagerConfig: {
    enabled: true,
    pageSize: 20,
    pageSizes: [10, 20, 50, 100],
  },
  columns: [
    { type: 'seq', width: 50, fixed: 'left' },
    { field: 'sku', title: 'SKU', width: 180, fixed: 'left', sortable: true },
    { field: 'product_name', title: '产品名称', minWidth: 200 },
    { field: 'warehouse_name', title: '仓库', width: 150 },
    { 
      field: 'quantity', 
      title: '库存总量', 
      width: 100, 
      align: 'center',
      sortable: true
    },
    { 
      field: 'allocated_quantity', 
      title: '已分配', 
      width: 100, 
      align: 'center',
      slots: { default: 'allocated_slot' }
    },
    { 
      field: 'available_quantity', 
      title: '可用库存', 
      width: 100, 
      align: 'center',
      slots: { default: 'available_slot' },
      sortable: true
    },
    { field: 'batch_no', title: '批次号', width: 120 },
    { field: 'location_code', title: '库位', width: 100 },
    { field: 'updated_at', title: '更新时间', width: 160 },
  ],
  toolbarConfig: {
    refresh: true,
    custom: true,
    slots: { buttons: 'toolbar_buttons' }
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const res = await getStockList({
            page: page.currentPage,
            per_page: page.pageSize,
            sku: searchSku.value,
            warehouse_id: searchWarehouseId.value,
          });
          return res;
        } catch (error) {
          console.error(error);
          return { items: [], total: 0 };
        }
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

// --- Handlers ---

async function loadWarehouses() {
  try {
    const res = await getWarehouseList({ per_page: 100 });
    warehouseOptions.value = res.items.map((w: Warehouse) => ({
      label: w.name,
      value: w.id,
    }));
  } catch (error) {
    console.error('Failed to load warehouses', error);
  }
}

function handleSearch() {
  gridApi.reload();
}

function handleReset() {
  searchSku.value = '';
  searchWarehouseId.value = undefined;
  gridApi.reload();
}

onMounted(() => {
  loadWarehouses();
  // Grid auto-loads via proxyConfig
});
</script>

<template>
  <Page auto-content-height title="库存查询">
    <Grid>
      <template #toolbar_buttons>
        <Space>
          <Input
            v-model:value="searchSku"
            placeholder="SKU"
            style="width: 200px"
            @press-enter="handleSearch"
          />
          <Select
            v-model:value="searchWarehouseId"
            placeholder="选择仓库"
            style="width: 200px"
            allow-clear
            :options="warehouseOptions"
            @change="handleSearch"
          />
          <AButton type="primary" @click="handleSearch">
            <SearchOutlined /> 查询
          </AButton>
          <AButton @click="handleReset">
            重置
          </AButton>
        </Space>
      </template>

      <template #allocated_slot="{ row }">
        <span :class="row.allocated_quantity > 0 ? 'text-orange-500 font-medium' : 'text-gray-400'">
          {{ row.allocated_quantity }}
        </span>
      </template>

      <template #available_slot="{ row }">
        <Tag :color="row.available_quantity > 0 ? 'success' : 'error'">
          {{ row.available_quantity }}
        </Tag>
      </template>
    </Grid>
  </Page>
</template>

