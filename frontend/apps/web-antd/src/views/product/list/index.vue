<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getProductListApi, deleteProduct } from '#/api/core/product';
import type { Product } from '#/api/core/product';
import { onMounted, ref } from 'vue';
import { Button as AButton, Popconfirm, message, Space, Tag } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import { useRouter } from 'vue-router';

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
      width: 180, 
      fixed: 'left', 
      sortable: true,
      slots: { default: 'spu_code_slot' } 
    },
    { field: 'name', title: '产品名称', minWidth: 200, showOverflow: true },
    { 
      field: 'category_name', 
      title: '所属分类', 
      width: 150,
      formatter: ({ row }) => row.category?.name || '-'
    },
    {
      field: 'variant_count',
      title: '变体数 (SKU)',
      width: 100,
      align: 'center',
      formatter: ({ row }) => row.variants?.length || 0
    },
    { 
      field: 'created_at', 
      title: '创建时间', 
      width: 160,
      formatter: ({ cellValue }) => cellValue ? new Date(cellValue).toLocaleDateString() : '-'
    },
    {
      title: '操作',
      width: 180,
      fixed: 'right',
      slots: { default: 'action_slot' }
    }
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const res = await getProductListApi({
            page: page.currentPage,
            per_page: page.pageSize,
          });
          return { items: res.items, total: res.total };
        } catch (e) {
          console.error('Failed to load products:', e);
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

// --- Actions ---

function handleCreate() {
  router.push('/product/create'); // We will define this route later
}

function handleEdit(row: Product) {
  router.push(`/product/edit/${row.id}`);
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
});
</script>

<template>
  <Page auto-content-height title="产品列表 (SPU)">
    <Grid>
      <template #toolbar_buttons>
        <AButton type="primary" @click="handleCreate">
           <PlusOutlined /> 新增产品
        </AButton>
      </template>

      <template #spu_code_slot="{ row }">
        <span class="font-mono font-bold text-primary cursor-pointer hover:underline" @click="handleEdit(row)">
          {{ row.spu_code }}
        </span>
      </template>

      <template #action_slot="{ row }">
        <Space>
           <AButton type="link" size="small" @click="handleEdit(row)">
             <EditOutlined /> 编辑
           </AButton>
           <Popconfirm title="确定删除该产品?" @confirm="handleDelete(row)">
             <AButton type="link" size="small" danger>
               <DeleteOutlined /> 删除
             </AButton>
           </Popconfirm>
        </Space>
      </template>
    </Grid>
  </Page>
</template>

