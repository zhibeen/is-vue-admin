<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getDeclarationListApi, generateContractsApi, getDeclarationStatsApi } from '#/api/customs/declaration';
import { useVbenModal } from '@vben/common-ui';
import ImportModal from './ImportModal.vue';
import { message, Modal, Tag, Button, Card } from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import { useRouter } from 'vue-router';
import { ref, onMounted } from 'vue';
import { 
    FileOutlined, 
    AuditOutlined, 
    SendOutlined, 
    CheckCircleOutlined, 
    ContainerOutlined, 
    WarningOutlined, 
    FileDoneOutlined,
    RightOutlined 
} from '@ant-design/icons-vue';

import type { VbenFormProps } from '#/adapter/form';

const router = useRouter();

const [ImportDeclModal, importModalApi] = useVbenModal({
  connectedComponent: ImportModal,
});

// --- Status Bar Logic ---
const currentStatus = ref('all');
const statsMap = ref<Record<string, number>>({});

const flowStatus = [
  { label: '草稿', value: 'draft', icon: FileOutlined, color: 'text-gray-500' },
  { label: '待审核', value: 'pending', icon: AuditOutlined, color: 'text-blue-500' },
  { label: '已申报', value: 'declared', icon: SendOutlined, color: 'text-orange-500' },
  { label: '已放行', value: 'cleared', icon: CheckCircleOutlined, color: 'text-green-500' },
  { label: '已归档', value: 'archived', icon: ContainerOutlined, color: 'text-cyan-500' },
];

const exceptionStatus = [
  { label: '修撤中', value: 'amending', icon: WarningOutlined, color: 'text-red-500' },
  { label: '修改已批准', value: 'amended', icon: FileDoneOutlined, color: 'text-purple-500' },
];

async function loadStats() {
    try {
        const res = await getDeclarationStatsApi();
        const map: Record<string, number> = {};
        res.forEach(item => {
            map[item.status] = item.count;
        });
        statsMap.value = map;
    } catch (e) {
        console.error(e);
    }
}

async function handleStatusClick(status: string) {
    if (currentStatus.value === status) {
        currentStatus.value = 'all'; 
    } else {
        currentStatus.value = status;
    }
    console.log('currentStatus', currentStatus.value);
    // Update grid form
    // Use '' (empty string) to force clear the value. 
    // Vben form/AntD might ignore null/undefined in setValues for merging, 
    // but empty string is usually treated as a valid value update.
    const nextValue = currentStatus.value === 'all' ? '' : currentStatus.value;
    await gridApi.formApi.setValues({ status: nextValue });
    
    // Force reload with new params to ensure query is updated
    await gridApi.formApi.submitForm();
}

onMounted(() => {
    loadStats();
});

// --- Grid Configuration ---

const formOptions: VbenFormProps = {
  schema: [
    {
      fieldName: 'search_no',
      label: '编号搜索',
      component: 'Input',
      componentProps: {
        placeholder: '支持模糊搜索：预录入编号/报关单单号',
        allowClear: true,
      },
      colProps: { span: 8 },
    },
    {
      fieldName: 'pre_entry_no',
      label: '预录入编号',
      component: 'Input',
      componentProps: {
        placeholder: '精确搜索：HR-YL-2412-0001',
        allowClear: true,
      },
      colProps: { span: 6 },
    },
    {
      fieldName: 'status',
      label: '状态',
      component: 'Select',
      componentProps: {
        options: [
          { label: '草稿', value: 'draft' },
          { label: '待审核', value: 'pending' },
          { label: '已申报', value: 'declared' },
          { label: '已放行', value: 'cleared' },
          { label: '修撤中', value: 'amending' },
          { label: '修改已批准', value: 'amended' },
          { label: '已归档', value: 'archived' },
        ],
        placeholder: '请选择状态',
        allowClear: true,
        mode: 'multiple',
      },
      colProps: { span: 6 },
    },
    {
      fieldName: 'container_mode',
      label: '货柜模式',
      component: 'Select',
      componentProps: {
        options: [
            { label: '整柜 (FCL)', value: 'FCL' },
            { label: '散货 (LCL)', value: 'LCL' },
        ],
        allowClear: true,
      },
      colProps: { span: 4 },
    },
    {
      fieldName: 'export_date',
      label: '出口日期',
      component: 'RangePicker',
      componentProps: {
        valueFormat: 'YYYY-MM-DD',
        allowClear: true,
      },
      colProps: { span: 8 },
    },
  ],
  collapsedRows: 1, 
  showCollapseButton: true,
  submitOnReset: true,
};

const gridOptions: VxeGridProps = {
  id: 'customs_declaration_list_v2',  // 修改 ID 强制清除缓存
  customConfig: {
    storage: true,
  },
  columns: [
    { field: 'marks_and_notes', title: '备注', width: 150 },
    { field: 'pre_entry_no', title: '预录入编号', width: 180, fixed: 'left', slots: { default: 'entry_no_link' }, formatter: ({ cellValue }) => cellValue || '-' },
    { field: 'customs_no', title: '报关单单号', width: 150, formatter: ({ cellValue }) => cellValue || '-' },
    { field: 'internal_shipper_name', title: '生产销售单位', width: 200 },
    { field: 'overseas_consignee', title: '境外收货人', width: 150 },
    { field: 'contract_no', title: '合同编号', width: 150 },
    { field: 'export_date', title: '出口日期', width: 120, sortable: true },
    { field: 'destination_country', title: '运抵国', width: 120 },
    { field: 'source_type', title: '关联单据类型', width: 120, formatter: ({ cellValue }) => {
        const map: any = { manual: '手工录入', excel_import: 'Excel导入', api: 'API推送' };
        return map[cellValue] || cellValue;
    }},
    { field: 'bill_of_lading_no', title: '关联单据号', width: 150 },
    { field: 'product_count', title: '商品数', width: 80, align: 'center' },
    { field: 'pack_count', title: '总箱数', width: 80, align: 'center' },
    { field: 'net_weight', title: '总净重(kg)', width: 100, align: 'right' },
    { field: 'gross_weight', title: '总毛重(kg)', width: 100, align: 'right' },
    { field: 'freight', title: '运费', width: 100, align: 'right' },
    { field: 'insurance', title: '保费', width: 100, align: 'right' },
    { field: 'incidental', title: '杂费', width: 100, align: 'right' },
    { field: 'fob_total', title: '总商品金额', minWidth: 120, align: 'right', headerTooltip: true, titlePrefix: { content: 'FOB总价(不含运保费)' }, formatter: ({ cellValue }) => {
        return cellValue ? `$${Number(cellValue).toFixed(2)}` : '';
    }},
    { field: 'created_at', title: '创建时间', width: 150 },
    { field: 'status', title: '状态', width: 100, fixed: 'right', slots: { default: 'status' }, formatter: ({ cellValue }) => {
        const map: any = { 
            draft: '草稿', 
            pending: '待审核', 
            declared: '已申报', 
            cleared: '已放行',
            amending: '修撤中',
            amended: '修改已批准',
            archived: '已归档'
        };
        return map[cellValue] || cellValue;
    }},
    { title: '操作', width: 180, slots: { default: 'action' }, fixed: 'right', field: 'action' },
  ],
  pagerConfig: {
    enabled: true,
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        const params: any = {
            page: page.currentPage,
            per_page: page.pageSize,
            ...formValues,
        };
        
        if (formValues.export_date && Array.isArray(formValues.export_date)) {
            params.start_date = formValues.export_date[0];
            params.end_date = formValues.export_date[1];
            delete params.export_date;
        }

        if (Array.isArray(params.status)) {
            params.status = params.status.join(',');
        }

        return await getDeclarationListApi(params);
      },
    },
  },
  toolbarConfig: {
    custom: true,
    slots: { buttons: 'toolbar_buttons' },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions,
  formOptions,
});

function openImportModal() {
    importModalApi.open();
}

function openDetail(row: any) {
    router.push({ name: 'DeclarationDetail', params: { id: row.id } });
}

async function handleGenerateContracts(row: any) {
    Modal.confirm({
        title: '确认生成交付合同?',
        content: `系统将根据供应商自动拆分报关单 ${row.pre_entry_no || row.id}，生成对应的交付合同草稿。`,
        okText: '确认生成',
        cancelText: '取消',
        onOk: async () => {
            try {
                const res = await generateContractsApi(row.id);
                message.success(res.message);
                gridApi.reload();
                loadStats();
            } catch(e) {
                console.error(e);
            }
        }
    });
}
</script>

<template>
  <Page>
    <div class="p-4 h-full flex flex-col gap-4">
    
      <!-- Status Overview Bar -->
      <Card :bordered="false" size="small">
        <div class="flex flex-wrap gap-4 items-center">
            <!-- Main Flow -->
            <div class="flex items-center gap-2">
                <template v-for="(step, index) in flowStatus" :key="step.value">
                    <div 
                        class="cursor-pointer px-4 py-2 rounded border transition-all flex items-center gap-2 hover:shadow-sm"
                        :class="[
                            currentStatus === step.value 
                                ? 'border-primary bg-primary/10 text-primary' 
                                : 'border-gray-200 dark:border-gray-700 hover:border-primary/50 text-gray-600 dark:text-gray-300'
                        ]"
                        @click="handleStatusClick(step.value)"
                    >
                        <component :is="step.icon" class="text-lg" :class="currentStatus === step.value ? '' : step.color" />
                        <div class="flex flex-col items-start">
                            <span class="text-xs font-bold">{{ step.label }}</span>
                        </div>
                        <span class="text-xs bg-gray-100 dark:bg-gray-700 px-1.5 rounded-full ml-1" v-if="statsMap[step.value]">{{ statsMap[step.value] }}</span>
                    </div>
                    <!-- Arrow -->
                    <RightOutlined v-if="index < flowStatus.length - 1" class="text-gray-300 dark:text-gray-600 text-xs" />
                </template>
            </div>
            
            <div class="w-px h-8 bg-gray-200 dark:bg-gray-700 mx-2 hidden md:block"></div>

            <!-- Exception Flow -->
            <div class="flex items-center gap-2">
                 <template v-for="step in exceptionStatus" :key="step.value">
                    <div 
                        class="cursor-pointer px-4 py-2 rounded border transition-all flex items-center gap-2 hover:shadow-sm"
                         :class="[
                            currentStatus === step.value 
                                ? 'border-red-500 bg-red-50 dark:bg-red-900/20 text-red-500' 
                                : 'border-gray-200 dark:border-gray-700 hover:border-red-200 text-gray-600 dark:text-gray-300'
                        ]"
                        @click="handleStatusClick(step.value)"
                    >
                        <component :is="step.icon" class="text-lg" :class="currentStatus === step.value ? '' : step.color" />
                         <div class="flex flex-col items-start">
                            <span class="text-xs font-bold">{{ step.label }}</span>
                        </div>
                        <span class="text-xs bg-gray-100 dark:bg-gray-700 px-1.5 rounded-full ml-1" v-if="statsMap[step.value]">{{ statsMap[step.value] }}</span>
                    </div>
                 </template>
            </div>
        </div>
      </Card>

      <Card :bordered="false" class="flex-1" :bodyStyle="{ height: '100%', padding: '0' }">
        <Grid>
            <template #toolbar_buttons>
                <Button type="primary" @click="openImportModal">导入装箱单</Button>
            </template>
            
            <template #entry_no_link="{ row }">
                <Button type="link" size="small" class="p-0" @click="openDetail(row)">{{ row.pre_entry_no || '-' }}</Button>
            </template>

            <template #status="{ row }">
                <Tag v-if="row.status === 'draft'" color="default">草稿</Tag>
                <Tag v-else-if="row.status === 'pending'" color="processing">待审核</Tag>
                <Tag v-else-if="row.status === 'declared'" color="warning">已申报</Tag>
                <Tag v-else-if="row.status === 'cleared'" color="success">已放行</Tag>
                <Tag v-else-if="row.status === 'amending'" color="error">修撤中</Tag>
                <Tag v-else-if="row.status === 'amended'" color="purple">修改已批准</Tag>
                <Tag v-else-if="row.status === 'archived'" color="cyan">已归档</Tag>
                <Tag v-else>{{ row.status }}</Tag>
            </template>

            <template #action="{ row }">
                <Button type="link" size="small" v-if="row.status === 'draft'" @click="handleGenerateContracts(row)">生成合同</Button>
                <Button type="link" size="small" @click="openDetail(row)">详情</Button>
            </template>
        </Grid>
      </Card>
      
      <ImportDeclModal @success="() => { gridApi.reload(); loadStats(); }" />
    </div>
  </Page>
</template>>