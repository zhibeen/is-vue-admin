<script setup lang="ts">
import { useVbenModal, useVbenDrawer } from '@vben/common-ui';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getContractList, printContracts, exportContracts } from '#/api/serc/supply';
import { getSupplierList } from '#/api/purchase/supplier';
import { getCompanyList } from '#/api/serc/foundation';
import { Button, Tag, Popconfirm, message, Progress, Modal, Input, Radio } from 'ant-design-vue';
import { onMounted, ref } from 'vue';
import { Page } from '@vben/common-ui';
import type { VbenFormProps } from '#/adapter/form';
import ContractCreateModal from './ContractCreateModal.vue';
import ContractDetailDrawer from './ContractDetailDrawer.vue';
import SupplyContractBuilder from './SupplyContractBuilder.vue'; // New component

// --- Form Configuration ---
const formOptions: VbenFormProps = {
  collapsed: false,
  schema: [
    {
      component: 'Input',
      fieldName: 'contract_no',
      label: '合同编号',
    },
    {
      component: 'Select',
      fieldName: 'company_id',
      label: '采购主体',
      componentProps: {
        options: [],
        fieldNames: { label: 'short_name', value: 'id' },
        showSearch: true,
        optionFilterProp: 'label',
        allowClear: true,
      },
    },
    {
      component: 'Select',
      fieldName: 'supplier_id',
      label: '供应商',
      componentProps: {
        options: [],
        fieldNames: { label: 'name', value: 'id' },
        showSearch: true,
        optionFilterProp: 'label',
        allowClear: true,
      },
    },
    {
      component: 'Select',
      fieldName: 'status',
      label: '状态',
      componentProps: {
        options: [
          { label: '待处理', value: 'pending' },
          { label: '结算中', value: 'settling' },
          { label: '已结算', value: 'settled' },
        ],
        allowClear: true,
      },
    },
  ],
  showCollapseButton: true,
  submitButtonOptions: { content: '查询' },
  resetButtonOptions: { content: '重置' },
};

// --- Grid Configuration ---
const gridOptions: VxeGridProps = {
  columns: [
    { type: 'checkbox', width: 50, fixed: 'left' },
    { type: 'seq', width: 50, align: 'center', fixed: 'left', resizable: false }, 
    { field: 'contract_no', title: '合同编号', minWidth: 180, fixed: 'left' },
    { field: 'company_name', title: '采购主体', minWidth: 120, showOverflow: true },
    { field: 'supplier_name', title: '供应商', minWidth: 200, showOverflow: true },
    { 
      field: 'total_amount', 
      title: '合同总额', 
      minWidth: 120, 
      align: 'right',
      formatter: ({ cellValue }) => {
        return cellValue ? `￥${Number(cellValue).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}` : '￥0.00';
      } 
    },
    {
      title: '付款进度',
      minWidth: 180, 
      slots: { default: 'payment_default' } 
    },
    { 
      field: 'status', 
      title: '业务状态', 
      width: 100,
      align: 'center',
      slots: { default: 'status_default' } 
    },
    { field: 'created_at', title: '创建日期', width: 120, align: 'center' },
    { 
      title: '操作', 
      width: 140, 
      fixed: 'right', 
      align: 'center',
      slots: { default: 'action_default' } 
    },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        const res = await getContractList({
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
  height: 'auto',
  pagerConfig: {
    enabled: true,
  },
  toolbarConfig: {
    custom: true,
    // export: true, // Removed standard export
    refresh: true,
    resizable: true,
    zoom: true,
    slots: { buttons: 'toolbar_buttons' },
  },
  showOverflow: true,
  border: true,
  stripe: true,
};

const [Grid, gridApi] = useVbenVxeGrid({ 
  gridOptions,
  formOptions,
});

// --- Export State & Logic ---
const exportModalVisible = ref(false);
const exportFilename = ref('');
const exportMode = ref('all'); // 'all' (filtered) or 'selected'
const exportLoading = ref(false);

function handleOpenExportModal() {
    exportFilename.value = `采购合同报表_${new Date().toISOString().slice(0,10)}`;
    
    // Smart default mode based on selection
    const selectedRecords = gridApi.grid.getCheckboxRecords();
    if (selectedRecords && selectedRecords.length > 0) {
        exportMode.value = 'selected';
    } else {
        exportMode.value = 'all';
    }
    
    exportModalVisible.value = true;
}

async function handleExportConfirm() {
    exportLoading.value = true;
    try {
        const payload: any = {};
        const formValues = await gridApi.formApi.getValues();
        
        if (exportMode.value === 'selected') {
            const records = gridApi.grid.getCheckboxRecords();
            payload.ids = records.map((item: any) => item.id);
            if (payload.ids.length === 0) {
                 message.warning('请先勾选数据');
                 exportLoading.value = false;
                 return;
            }
        } else {
            // 'all' -> export all matching filters
            Object.assign(payload, formValues);
        }
        
        const blob = await exportContracts(payload);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        let downloadName = exportFilename.value || `采购合同报表_${new Date().toISOString().slice(0,10)}`;
        if (!downloadName.endsWith('.xlsx')) {
            downloadName += '.xlsx';
        }
        link.download = downloadName;

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        message.success('导出成功');
        exportModalVisible.value = false;
    } catch (e) {
        console.error(e);
        message.error('导出失败');
    } finally {
        exportLoading.value = false;
    }
}

// --- Handlers ---

onMounted(async () => {
  const supplierRes = await getSupplierList();
  const companyRes = await getCompanyList(); 

  gridApi.formApi.updateSchema([
    {
      fieldName: 'company_id',
      componentProps: { options: companyRes }, 
    },
    {
      fieldName: 'supplier_id',
      componentProps: { options: supplierRes.items },
    }
  ]);
});

// --- Create Modal ---
const [CreateModal, modalApi] = useVbenModal({
  connectedComponent: ContractCreateModal,
});

// --- Detail Drawer ---
const [DetailDrawer, drawerApi] = useVbenDrawer({
  connectedComponent: ContractDetailDrawer,
});

// --- Supply Contract Builder ---
const [BuilderDrawer, builderApi] = useVbenDrawer({
  connectedComponent: SupplyContractBuilder,
});

function handleCreate() {
  modalApi.open();
}

function handleGenerateStatement(row: any) {
  builderApi.setData({ l1Contract: row });
  builderApi.open();
}

function handleCreateSuccess() {
  gridApi.reload();
}

function handleView(row: any) {
  drawerApi.setData({ row });
  drawerApi.open();
}

function handleDelete(row: any) {
    message.success(`模拟删除成功: ${row.contract_no}`);
}

async function handlePrintBatch() {
  const selectedRows = gridApi.grid.getCheckboxRecords();
  if (!selectedRows.length) {
    message.warning('请先勾选要打印的合同');
    return;
  }
  const ids = selectedRows.map((row: any) => row.id);
  
  try {
    gridApi.setLoading(true);
    message.loading({ content: '正在生成合同文件...', key: 'print' });
    
    const response = await printContracts(ids);
    
    const blob = new Blob([response as any], { 
        type: (response as any).type || 'application/pdf' 
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const isZip = blob.type === 'application/zip';
    link.download = isZip ? 'Contracts_Batch.zip' : 'Contracts.pdf';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    message.success({ content: '下载成功', key: 'print' });
  } catch (e) {
    console.error(e);
    message.error({ content: '打印失败', key: 'print' });
  } finally {
    gridApi.setLoading(false);
  }
}
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <!-- Toolbar Buttons -->
      <template #toolbar_buttons>
        <Button type="primary" @click="handleCreate">
          手工录入合同(新)
        </Button>
        <Button class="ml-2" @click="handlePrintBatch">
          批量打印
        </Button>
        <Button class="ml-2" @click="handleOpenExportModal">
          导出 Excel
        </Button>
      </template>
      
      <!-- Payment Progress Column Slot -->
      <template #payment_default="{ row }">
        <div class="flex items-center w-full gap-2">
            <!-- 左侧：线性进度条 -->
            <div class="flex-1">
                <Progress 
                    :percent="Math.floor(((row.paid_amount || 0) / (row.total_amount || 1)) * 100)" 
                    :stroke-color="{ '0%': '#108ee9', '100%': '#87d068' }"
                    size="small" 
                    :show-info="false"
                    class="!m-0"
                />
            </div>

            <!-- 右侧：金额信息 -->
            <div class="flex flex-col text-right min-w-[80px]">
                <span class="text-xs text-gray-400 scale-90 origin-right mb-[2px]">已付</span>
                <span class="font-mono text-xs text-gray-700">￥{{ Number(row.paid_amount || 0).toLocaleString('zh-CN') }}</span>
            </div>
        </div>
      </template>

      <!-- Status Column Slot -->
      <template #status_default="{ row }">
        <Tag v-if="row.status === 'pending'" color="orange">待处理</Tag>
        <Tag v-else-if="row.status === 'settling'" color="blue">结算中</Tag>
        <Tag v-else-if="row.status === 'settled'" color="green">已结算</Tag>
        <Tag v-else>{{ row.status }}</Tag>
      </template>

      <!-- Action Column Slot -->
      <template #action_default="{ row }">
        <Button type="link" size="small" @click="handleView(row)">查看</Button>
        <!-- New Button: Prepare Statement -->
        <Button type="link" size="small" @click="handleGenerateStatement(row)">编制结算</Button>
        <Popconfirm title="确定要删除吗?" @confirm="handleDelete(row)">
           <Button type="link" danger size="small">删除</Button>
        </Popconfirm>
      </template>
    </Grid>
    
    <CreateModal @success="handleCreateSuccess" />
    <DetailDrawer />
    <BuilderDrawer /> <!-- Added -->

    <!-- Custom Export Modal -->
    <Modal
      v-model:open="exportModalVisible"
      title="导出合同报表"
      @ok="handleExportConfirm"
      :confirmLoading="exportLoading"
    >
      <div class="p-4">
        <div class="mb-4">
          <label class="block mb-2 font-medium">文件名:</label>
          <Input v-model:value="exportFilename" placeholder="请输入文件名" suffix=".xlsx" />
        </div>
        <div>
          <label class="block mb-2 font-medium">导出范围:</label>
          <Radio.Group v-model:value="exportMode">
            <Radio value="all">当前搜索结果 (全部)</Radio>
            <Radio value="selected">仅选中项</Radio>
          </Radio.Group>
        </div>
      </div>
    </Modal>
  </Page>
</template>
