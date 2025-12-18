<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Button, message, Space, Popconfirm, Tag } from 'ant-design-vue';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons-vue';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getCustomsProductList, deleteCustomsProduct, type CustomsProduct } from '#/api/customs/product';
import ProductModal from './ProductModal.vue';

// --- Grid Config ---
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 60 },
    { field: 'name', title: '报关名称', minWidth: 150 },
    { field: 'hs_code', title: 'HS编码', width: 120 },
    { field: 'rebate_rate', title: '退税率', width: 100 },
    { field: 'unit', title: '单位', width: 80 },
    { field: 'elements', title: '申报要素模板', minWidth: 200 },
    { field: 'is_active', title: '状态', width: 80, slots: { default: 'active' } },
    { title: '操作', width: 200, slots: { default: 'action' }, fixed: 'right' }
  ],
  data: [],
  pagerConfig: {
    enabled: true
  },
  toolbarConfig: {
    refresh: true,
    custom: true,
    buttons: [
      { code: 'add', name: '新建品类', status: 'primary', icon: 'vxe-icon-add' }
    ]
  },
  // height: 'auto', // Remove auto height from grid options to let Vben Page handle it via class
  proxyConfig: {
    autoLoad: true,
    response: {
      result: 'items',
      total: 'total'
    },
    ajax: {
      query: async ({ page }) => {
        return await getCustomsProductList({
          page: page.currentPage,
          per_page: page.pageSize
        });
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions,
  gridEvents: {
    toolbarToolClick: (params) => {
      if (params.code === 'add') handleAdd();
    }
  }
});

// --- State ---
const modalVisible = ref(false);
const editingRecord = ref<CustomsProduct | null>(null);

function handleAdd() {
  editingRecord.value = null;
  modalVisible.value = true;
}

function handleEdit(record: CustomsProduct) {
  editingRecord.value = { ...record };
  modalVisible.value = true;
}

async function handleDelete(record: CustomsProduct) {
  try {
    await deleteCustomsProduct(record.id);
    message.success('删除成功');
    await gridApi.query();
  } catch (e) {
    console.error(e);
  }
}

function handleModalSuccess() {
  modalVisible.value = false;
  gridApi.reload();
}
</script>

<template>
  <Page :auto-content-height="true">
    <Grid>
      <template #active="{ row }">
        <Tag v-if="row.is_active" color="success">启用</Tag>
        <Tag v-else color="error">禁用</Tag>
      </template>
      
      <template #action="{ row }">
        <Space>
          <Button type="link" size="small" @click="handleEdit(row)">
            <EditOutlined /> 编辑
          </Button>
          <Popconfirm title="确认删除?" @confirm="handleDelete(row)">
            <Button type="link" danger size="small">
              <DeleteOutlined /> 删除
            </Button>
          </Popconfirm>
        </Space>
      </template>
    </Grid>

    <ProductModal 
      v-model:open="modalVisible"
      :record="editingRecord"
      @success="handleModalSuccess"
    />
  </Page>
</template>

