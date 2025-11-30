<script setup lang="ts">
import { useVbenModal } from '@vben/common-ui';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { Button, Popconfirm, Tag, message } from 'ant-design-vue';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import type { VbenFormProps } from '#/adapter/form';

import { getSupplierList, deleteSupplier } from '#/api/purchase/supplier';
import type { SysSupplier } from '#/api/purchase/model';
import SupplierModal from './SupplierModal.vue';

const [Modal, modalApi] = useVbenModal({
  connectedComponent: SupplierModal,
});

// Formatters
const typeMap: Record<string, { text: string; color: string }> = {
  manufacturer: { text: '生产商', color: 'blue' },
  trader: { text: '贸易商', color: 'green' },
  service_provider: { text: '服务商', color: 'orange' },
  other: { text: '其他', color: 'default' }
};

const statusMap: Record<string, { text: string; color: string }> = {
  active: { text: '活跃', color: 'success' },
  inactive: { text: '停用', color: 'default' },
  blacklisted: { text: '黑名单', color: 'error' },
  potential: { text: '潜在', color: 'warning' }
};

const gradeColorMap: Record<string, string> = {
  'A': 'green',
  'B': 'blue',
  'C': 'orange',
  'D': 'red'
};

const formOptions: VbenFormProps = {
  collapsed: false,
  schema: [
    {
      component: 'Input',
      fieldName: 'q',
      label: '关键词',
      componentProps: {
        placeholder: '输入代码/名称/简称搜索',
        allowClear: true,
      },
    },
    {
      component: 'Select',
      fieldName: 'supplier_type',
      label: '类型',
      componentProps: {
        options: [
          { label: '生产商', value: 'manufacturer' },
          { label: '贸易商', value: 'trader' },
          { label: '服务商', value: 'service_provider' },
          { label: '其他', value: 'other' },
        ],
        placeholder: '请选择类型',
        allowClear: true,
      },
    },
    {
      component: 'Select',
      fieldName: 'status',
      label: '状态',
      componentProps: {
        options: [
          { label: '活跃', value: 'active' },
          { label: '停用', value: 'inactive' },
          { label: '黑名单', value: 'blacklisted' },
          { label: '潜在', value: 'potential' },
        ],
        placeholder: '请选择状态',
        allowClear: true,
      },
    },
  ],
  showCollapseButton: true,
  submitOnChange: false,
  submitOnEnter: true,
};

const gridOptions: VxeGridProps = {
  columns: [
    { field: 'code', title: '代码', width: 100, fixed: 'left' },
    { field: 'supplier_type', title: '类型', width: 100, slots: { default: 'type_slot' } },
    { 
      field: 'name', 
      title: '供应商名称', 
      minWidth: 200,
      slots: { default: 'name_slot' }
    },
    { field: 'short_name', title: '简称', width: 120 },
    { field: 'grade', title: '等级', width: 80, slots: { default: 'grade_slot' } },
    { field: 'status', title: '状态', width: 80, slots: { default: 'status_slot' } },
    { field: 'primary_contact', title: '首要联系人', minWidth: 100 },
    { field: 'primary_phone', title: '联系电话', minWidth: 120 },
    { field: 'payment_terms', title: '付款条款', minWidth: 150 }, // Added
    { field: 'currency', title: '币种', width: 80 },
    { 
      title: '操作', 
      width: 150, 
      fixed: 'right',
      slots: { default: 'action' }
    },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        try {
          const res = await getSupplierList({
            page: page.currentPage,
            per_page: page.pageSize,
            ...formValues,
          });
          return {
            items: res.items || [], 
            total: res.total || 0,
          };
        } catch (error) {
          console.error(error);
          return { items: [], total: 0 };
        }
      },
    },
  },
  height: 'auto',
  stripe: true,
  border: true,
  showOverflow: true,
  pagerConfig: {
    enabled: true,
    pageSizes: [10, 20, 50, 100],
    layouts: ['PrevPage', 'JumpNumber', 'NextPage', 'Sizes', 'Total'],
  },
  toolbarConfig: {
    custom: true,
    refresh: true,
    zoom: true,
    slots: { buttons: 'toolbar_buttons' },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ 
  gridOptions,
  formOptions, // 传入 formOptions 启用搜索表单
});

function handleAdd() {
  modalApi.setData({ isUpdate: false, data: null });
  modalApi.open();
}

function handleEdit(row: SysSupplier) {
  modalApi.setData({ isUpdate: true, data: row });
  modalApi.open();
}

async function handleDelete(row: SysSupplier) {
  try {
    await deleteSupplier(row.id);
    message.success('删除成功');
    gridApi.reload(); 
  } catch (error) {
    console.error(error);
    message.error('删除失败');
  }
}

function handleSuccess() {
  gridApi.reload();
}

function getNameColor(supplierType: string): string {
  const colorMap: Record<string, string> = {
    manufacturer: '#1890ff',    // 蓝色 - 生产商
    trader: '#52c41a',          // 绿色 - 贸易商
    service_provider: '#fa8c16', // 橙色 - 服务商
    other: '#8c8c8c'            // 灰色 - 其他
  };
  return colorMap[supplierType] || '#000000';
}
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar_buttons>
        <Button type="primary" @click="handleAdd">
          <PlusOutlined /> 新增供应商
        </Button>
      </template>

      <template #type_slot="{ row }">
        <Tag :color="typeMap[row.supplier_type]?.color">
          {{ typeMap[row.supplier_type]?.text || row.supplier_type }}
        </Tag>
      </template>

      <template #name_slot="{ row }">
        <span 
          class="font-medium"
          :style="{ color: getNameColor(row.supplier_type) }"
        >
          {{ row.name }}
        </span>
      </template>

      <template #grade_slot="{ row }">
        <Tag v-if="row.grade" :color="gradeColorMap[row.grade]">{{ row.grade }}</Tag>
      </template>

      <template #status_slot="{ row }">
        <Tag :color="statusMap[row.status]?.color">{{ statusMap[row.status]?.text || row.status }}</Tag>
      </template>

      <template #action="{ row }">
        <Button type="link" size="small" @click="handleEdit(row)">
          <EditOutlined /> 编辑
        </Button>
        <Popconfirm title="确认删除该供应商吗？" @confirm="handleDelete(row)">
          <Button type="link" size="small" danger>
            <DeleteOutlined /> 删除
          </Button>
        </Popconfirm>
      </template>
    </Grid>
    
    <Modal @success="handleSuccess" />
  </Page>
</template>

<style scoped>

</style>
