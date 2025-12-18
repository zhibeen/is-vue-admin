<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getDeclarationList, cancelMatch } from '#/api/serc/tax';
import { useVbenModal } from '@vben/common-ui';
import { Button, Tag, Popconfirm, message } from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import type { VbenFormProps } from '#/adapter/form';
import MatchModal from './MatchModal.vue';
import DeclarationDrawer from './DeclarationDrawer.vue';
import { useVbenDrawer } from '@vben/common-ui';

const formOptions: VbenFormProps = {
  collapsed: false,
  schema: [
    {
      component: 'Input',
      fieldName: 'entry_no',
      label: '报关单号',
    },
    {
      component: 'Select',
      fieldName: 'status',
      label: '状态',
      componentProps: {
        options: [
          { label: '草稿', value: 'draft' },
          { label: '预申报', value: 'pre_declared' },
          { label: '正式申报', value: 'official' },
        ],
        allowClear: true,
      },
    },
  ],
  showCollapseButton: true,
  submitButtonOptions: { content: '查询' },
  resetButtonOptions: { content: '重置' },
};

const gridOptions: VxeGridProps = {
  columns: [
    { field: 'entry_no', title: '报关单号', minWidth: 150 },
    { field: 'export_date', title: '出口日期', width: 120 },
    { field: 'destination_country', title: '目的国', width: 100 },
    { field: 'fob_total', title: 'FOB总额', width: 120, formatter: ({ cellValue }) => cellValue ? `$${Number(cellValue).toFixed(2)}` : '-' },
    { field: 'status', title: '状态', width: 100, slots: { default: 'status_default' } },
    { title: '操作', width: 200, fixed: 'right', slots: { default: 'action_default' } },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        const res = await getDeclarationList({
          page: page.currentPage,
          per_page: page.pageSize,
          ...formValues,
        });
        return {
          items: res.items || [],
          total: res.total || 0, 
        };
      },
    },
  },
  toolbarConfig: {
    refresh: true,
    zoom: true,
    slots: { buttons: 'toolbar_buttons' },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions, formOptions });

const [MatchModalComponent, matchModalApi] = useVbenModal({
  connectedComponent: MatchModal,
});

const [CreateDrawer, createDrawerApi] = useVbenDrawer({
  connectedComponent: DeclarationDrawer,
});

function handleMatch(row: any) {
  matchModalApi.setData({ id: row.id });
  matchModalApi.open();
}

function handleCreate() {
  createDrawerApi.open();
}

async function handleCancelMatch(row: any) {
  try {
    gridApi.setLoading(true);
    await cancelMatch(row.id);
    message.success('已解除匹配，发票额度已释放');
    gridApi.reload();
  } catch(e) {
    console.error(e);
  } finally {
    gridApi.setLoading(false);
  }
}
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar_buttons>
         <Button type="primary" @click="handleCreate">新建报关单</Button>
      </template>

      <template #status_default="{ row }">
        <Tag v-if="row.status === 'draft'" color="default">草稿</Tag>
        <Tag v-else-if="row.status === 'pre_declared'" color="orange">预申报</Tag>
        <Tag v-else-if="row.status === 'official'" color="green">已申报</Tag>
        <Tag v-else>{{ row.status }}</Tag>
      </template>

      <template #action_default="{ row }">
        <template v-if="row.status === 'draft'">
            <Button type="link" size="small" @click="handleMatch(row)">智能匹配</Button>
            <Button type="link" size="small">编辑</Button>
        </template>
        <template v-else-if="row.status === 'pre_declared'">
            <Button type="link" size="small">导出申报要素</Button>
             <Popconfirm title="确定要解除匹配吗? 发票额度将被释放。" @confirm="handleCancelMatch(row)">
                <Button type="link" danger size="small">解除匹配</Button>
             </Popconfirm>
        </template>
      </template>
    </Grid>
    <MatchModalComponent />
    <CreateDrawer />
  </Page>
</template>
