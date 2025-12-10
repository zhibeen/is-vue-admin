<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getHSCodeList, deleteHSCode } from '#/api/serc/foundation';
import { onMounted, ref } from 'vue';
import { Button as AButton, Drawer, Popconfirm, message, Space } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import type { SysHSCode } from '#/api/serc/model';
import HSCodeDrawer from './components/HSCodeDrawer.vue';

// --- 状态管理 ---
const showDetail = ref(false);
const currentItem = ref<SysHSCode | null>(null);
const drawerRef = ref(); // Edit/Create Drawer ref

// --- 表格配置 ---
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
      field: 'code', 
      title: 'HS编码', 
      width: 140, 
      fixed: 'left', 
      sortable: true,
      slots: { default: 'code_slot' } 
    },
    { field: 'name', title: '商品名称', minWidth: 200, showOverflow: true },
    
    // 分组：计量单位
    {
      title: '计量单位配置',
      children: [
        { field: 'unit_1', title: '第一法定', width: 90, align: 'center' },
        { field: 'unit_2', title: '第二法定', width: 90, align: 'center' },
        { 
          field: 'default_transaction_unit', 
          title: '建议申报', 
          width: 90, 
          align: 'center',
          className: 'bg-green-50/50' 
        },
      ]
    },

    // 分组：关键税率
    {
      title: '税率信息',
      children: [
        { 
          field: 'refund_rate', 
          title: '退税率', 
          width: 90, 
          align: 'right',
          formatter: ({ cellValue }) => cellValue ? `${(Number(cellValue) * 100).toFixed(0)}%` : '-' 
        },
        { 
          field: 'vat_rate', 
          title: '增值税', 
          width: 90,
          align: 'right',
          formatter: ({ cellValue }) => cellValue ? `${(Number(cellValue) * 100).toFixed(0)}%` : '-' 
        },
        { 
          field: 'import_mfn_rate', 
          title: '进口最惠国', 
          width: 110,
          align: 'right',
          formatter: ({ cellValue }) => cellValue ? `${(Number(cellValue) * 100).toFixed(0)}%` : '-' 
        },
      ]
    },

    // 分组：监管条件
    {
      title: '监管合规',
      children: [
        { field: 'regulatory_code', title: '监管证件', width: 100, showOverflow: true, align: 'center' },
        { field: 'inspection_code', title: '检疫类别', width: 100, align: 'center' },
      ]
    },
    
    // 操作列
    {
      title: '操作',
      width: 200, // Increased width for buttons
      fixed: 'right',
      slots: { default: 'action_slot' }
    }
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const res = await getHSCodeList();
          // 兼容处理
          const allData = Array.isArray(res) ? res : (res as any).data || [];
          
          // 前端分页
          const { currentPage, pageSize } = page;
          const startIndex = (currentPage - 1) * pageSize;
          const endIndex = startIndex + pageSize;
          const sliceData = allData.slice(startIndex, endIndex);
          
          return { items: sliceData, total: allData.length };
        } catch (e) {
          console.error('Failed to load HS codes:', e);
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

// --- 事件处理 ---

function handleView(row: SysHSCode) {
  currentItem.value = row;
  showDetail.value = true;
}

function handleAdd() {
  drawerRef.value?.open();
}

function handleEdit(row: SysHSCode) {
  drawerRef.value?.open(row);
}

async function handleDelete(row: SysHSCode) {
  try {
    await deleteHSCode(row.id);
    message.success('删除成功');
    gridApi.query();
  } catch (e) {
    // Error handled by interceptor usually
  }
}

function onDrawerSuccess() {
  gridApi.query();
}

onMounted(() => {
  // Grid auto queries
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <!-- 顶部工具栏按钮插槽 -->
      <template #toolbar_buttons>
        <AButton type="primary" @click="handleAdd" class="mr-2">
           <PlusOutlined /> 新增 HS 编码
        </AButton>
        <span class="text-gray-500 text-sm ml-2">
          💡 提示：双击行或点击详情查看完整申报要素
        </span>
      </template>

      <!-- HS编码列插槽 -->
      <template #code_slot="{ row }">
        <span class="font-mono font-bold text-primary cursor-pointer hover:underline" @click="handleView(row)">
          {{ row.code }}
        </span>
      </template>

      <!-- 操作列插槽 -->
      <template #action_slot="{ row }">
        <Space>
           <AButton type="link" size="small" @click="handleView(row)">详情</AButton>
           <AButton type="link" size="small" @click="handleEdit(row)">
             <EditOutlined /> 编辑
           </AButton>
           <Popconfirm title="确定删除该 HS 编码?" @confirm="handleDelete(row)">
             <AButton type="link" size="small" danger>
               <DeleteOutlined /> 删除
             </AButton>
           </Popconfirm>
        </Space>
      </template>
    </Grid>

    <!-- 详情抽屉 (View Only) -->
    <Drawer
      v-model:open="showDetail"
      title="HS 编码详情"
      width="600"
      placement="right"
    >
      <div v-if="currentItem" class="flex flex-col gap-6">
        
        <!-- 基础信息卡片 -->
        <div class="bg-gray-50 p-4 rounded-lg border border-gray-100">
          <div class="text-lg font-bold font-mono text-primary mb-2">{{ currentItem.code }}</div>
          <div class="text-base text-gray-800 font-medium">{{ currentItem.name }}</div>
        </div>

        <!-- 申报要素 (核心) -->
        <div>
          <h3 class="text-sm font-bold text-gray-500 mb-2 uppercase">申报要素 (Declaration Elements)</h3>
          <div class="p-3 bg-blue-50 text-blue-900 rounded border border-blue-100 text-sm leading-relaxed whitespace-pre-wrap">
            {{ currentItem.elements || '暂无申报要素信息' }}
          </div>
        </div>

        <!-- 详情 Grid -->
        <div class="grid grid-cols-2 gap-y-4 gap-x-8">
          
          <div class="col-span-2 border-b border-gray-100 pb-2 mb-2 font-bold text-gray-700">税率详情</div>
          
          <div class="flex flex-col">
            <span class="text-xs text-gray-400">出口退税率</span>
            <span class="font-mono text-lg">{{ currentItem.refund_rate ? (currentItem.refund_rate * 100).toFixed(0) + '%' : '-' }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-xs text-gray-400">增值税率</span>
            <span class="font-mono text-lg">{{ currentItem.vat_rate ? (currentItem.vat_rate * 100).toFixed(0) + '%' : '-' }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-xs text-gray-400">进口最惠国税率</span>
            <span class="font-mono text-lg">{{ currentItem.import_mfn_rate ? (currentItem.import_mfn_rate * 100).toFixed(0) + '%' : '-' }}</span>
          </div>
           <div class="flex flex-col">
            <span class="text-xs text-gray-400">进口普通税率</span>
            <span class="font-mono text-lg">{{ currentItem.import_general_rate ? (currentItem.import_general_rate * 100).toFixed(0) + '%' : '-' }}</span>
          </div>

          <div class="col-span-2 border-b border-gray-100 pb-2 mb-2 mt-4 font-bold text-gray-700">单位与监管</div>

          <div class="flex flex-col">
            <span class="text-xs text-gray-400">法定单位 (第一/第二)</span>
            <span>
              {{ currentItem.unit_1 || '-' }} 
              <span v-if="currentItem.unit_2">/ {{ currentItem.unit_2 }}</span>
            </span>
          </div>
           <div class="flex flex-col">
            <span class="text-xs text-gray-400">建议申报单位</span>
            <span class="font-bold text-green-600">{{ currentItem.default_transaction_unit || '-' }}</span>
          </div>

          <div class="flex flex-col">
            <span class="text-xs text-gray-400">监管证件代码</span>
            <span class="font-mono">{{ currentItem.regulatory_code || '无' }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-xs text-gray-400">检验检疫类别</span>
            <span class="font-mono">{{ currentItem.inspection_code || '无' }}</span>
          </div>
          
        </div>

        <!-- 备注 -->
        <div v-if="currentItem.note">
          <h3 class="text-sm font-bold text-gray-500 mb-2 uppercase">备注</h3>
          <div class="text-gray-600 text-sm">{{ currentItem.note }}</div>
        </div>

      </div>
    </Drawer>
    
    <!-- Edit/Create Drawer -->
    <HSCodeDrawer ref="drawerRef" @success="onDrawerSuccess" />
  </Page>
</template>

<style scoped>
/* 可选：微调样式 */
</style>
