<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getProductList, deleteProduct } from '#/api/core/product';
import { onMounted, ref } from 'vue';
import { Button as AButton, Popconfirm, message, Space, Tag } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import { useRouter } from 'vue-router';
import type { Product } from '#/api/core/product';

const router = useRouter();

// --- Grid Config ---
const gridOptions: VxeGridProps = {
  keepSource: true,
  height: 'auto',
  pagerConfig: {
    enabled: true,
    pageSize: 20,
    pageSizes: [10, 20, 50, 100],
  },
  columns: [
    { type: 'seq', width: 50, fixed: 'left' },
    { 
      field: 'spu_code', 
      title: 'SPU 编码', 
      minWidth: 180, 
      fixed: 'left', 
      sortable: true,
      slots: { default: 'spu_code_slot' } 
    },
    { field: 'name', title: '产品名称', minWidth: 250 },
    { field: 'category_name', title: '分类', width: 120 },
    /*
    { field: 'brand', title: '品牌', width: 100 },
    { field: 'model', title: '车型', width: 100 },
    { field: 'year', title: '年份', width: 100 },
    */
    { 
      field: 'variants_count', 
      title: '变体数', 
      width: 80, 
      align: 'center',
      slots: { default: 'variants_count_slot' }
    },
    { 
      field: 'is_active', 
      title: '状态', 
      width: 80, 
      align: 'center',
      slots: { default: 'status_slot' }
    },
    { field: 'created_at', title: '创建时间', width: 160 },
    {
      title: '操作',
      width: 280,
      fixed: 'right',
      slots: { default: 'action_slot' }
    }
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const res = await getProductList({
            page: page.currentPage,
            pageSize: page.pageSize,
          });
          // Assuming backend returns { items: [], total: N } structure for standard pagination
          // If using apiflask pagination defaults, it might be in `data.items` etc. 
          // Based on previous fixes, let's be robust.
          const data = (res as any).data || res;
          const items = Array.isArray(data) ? data : (data.items || []);
          const total = Array.isArray(data) ? data.length : (data.total || 0);
          
          return { items, total };
        } catch (e) {
          console.error(e);
          return { items: [], total: 0 };
        }
      },
    },
  },
  toolbarConfig: {
    refresh: true,
    zoom: true,
    custom: true,
    slots: { buttons: 'toolbar_buttons' }
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

// --- Handlers ---

function handleAdd() {
  router.push('/product/spu/create');
}

function handleView(row: Product) {
  router.push(`/product/spu/detail/${row.id}`); // View mode
}

function handleEdit(row: Product) {
  router.push(`/product/spu/edit/${row.id}`); // Edit mode
}

async function handleDelete(row: Product) {
  try {
    await deleteProduct(row.id);
    message.success('删除成功');
    gridApi.query();
  } catch (e) {
    // Error handled
  }
}

onMounted(() => {
  // Init
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar_buttons>
        <AButton type="primary" @click="handleAdd">
          <PlusOutlined /> 新建产品 (SPU)
        </AButton>
      </template>

      <template #spu_code_slot="{ row }">
        <span class="font-mono font-bold text-primary cursor-pointer hover:underline" @click="handleEdit(row)">
          {{ row.spu_code }}
        </span>
      </template>
      
      <template #variants_count_slot="{ row }">
        <Tag color="blue">{{ row.variants_count || 0 }}</Tag>
      </template>

      <template #status_slot="{ row }">
        <Tag :color="row.is_active ? 'success' : 'error'">
          {{ row.is_active ? '启用' : '停用' }}
        </Tag>
      </template>

      <template #action_slot="{ row }">
        <Space>
          <AButton type="link" size="small" @click="handleView(row)">
            <EyeOutlined /> 详情
          </AButton>
          <AButton type="link" size="small" @click="handleEdit(row)">
            <EditOutlined /> 编辑
          </AButton>
          <Popconfirm title="确定删除该产品? 这将同时删除所有关联 SKU。" @confirm="handleDelete(row)">
            <AButton type="link" size="small" danger>
              <DeleteOutlined /> 删除
            </AButton>
          </Popconfirm>
        </Space>
      </template>
    </Grid>
  </Page>
</template>

