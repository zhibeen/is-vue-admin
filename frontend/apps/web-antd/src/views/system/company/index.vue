<script setup lang="ts">
import { useVbenModal } from '@vben/common-ui';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getCompanyList, deleteCompany } from '#/api/serc/foundation';
import { onMounted } from 'vue';
import { Button, Popconfirm, message, Tag } from 'ant-design-vue';
import CompanyModal from './CompanyModal.vue';
import type { SysCompany } from '#/api/serc/model';

const [Modal, modalApi] = useVbenModal({
  connectedComponent: CompanyModal,
});

const gridOptions: VxeGridProps = {
  columns: [
    { 
      field: 'id', 
      title: 'ID', 
      width: 80,
      align: 'center',
    },
    { 
      field: 'legal_name', 
      title: '公司名称', 
      minWidth: 300,
      slots: { default: 'company_name' },
    },
    { 
      field: 'short_name', 
      title: '简称', 
      width: 100,
      showOverflow: 'tooltip',
    },
    { 
      field: 'unified_social_credit_code', 
      title: '统一社会信用代码', 
      width: 180,
      showOverflow: 'tooltip',
    },
    { 
      field: 'customs_code', 
      title: '海关编码', 
      width: 120,
      showOverflow: 'tooltip',
    },
    { 
      field: 'contact_person', 
      title: '联系人', 
      width: 90,
    },
    { 
      field: 'contact_phone', 
      title: '联系电话', 
      width: 120,
    },
    { 
      field: 'default_currency', 
      title: '默认币种', 
      width: 100,
      align: 'center',
    },
    { 
      field: 'status', 
      title: '状态', 
      width: 100,
      align: 'center',
      slots: { default: 'status' },
    },
    {
      title: '操作',
      width: 150,
      fixed: 'right',
      align: 'center',
      slots: { default: 'action' },
    },
  ],
  data: [], 
  height: '100%', // 使用百分比高度，配合外层容器的 flex 布局
  stripe: true,
  border: true,
  showOverflow: true,
  pagerConfig: {
    enabled: false,
  },
  toolbarConfig: {
    custom: true,
    export: true,
    refresh: true,
    zoom: true,
    refreshOptions: {
      icon: 'vxe-icon-refresh',
    },
    zoomOptions: {
      iconIn: 'vxe-icon-fullscreen',
      iconOut: 'vxe-icon-minimize',
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ 
  gridOptions,
  gridEvents: {
    // 绑定 toolbar 的刷新事件
    toolbarToolClick: (params: any) => {
      if (params.code === 'refresh') {
        loadData();
      }
    }
  }
});

async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getCompanyList();
    console.log('公司数据:', res); // 调试用
    // 显式设置数据
    gridApi.setGridOptions({ data: res });
  } catch (e) {
    console.error('加载公司数据失败:', e);
    message.error('加载数据失败');
  } finally {
    gridApi.setLoading(false);
  }
}

function handleCreate() {
  modalApi.setData({});
  modalApi.open();
}

function handleEdit(row: SysCompany) {
  modalApi.setData(row);
  modalApi.open();
}

async function handleDelete(row: SysCompany) {
  try {
    await deleteCompany(row.id);
    message.success('删除成功');
    loadData();
  } catch (e) {
    console.error('删除失败:', e);
    message.error('删除失败');
  }
}

function handleSuccess() {
  loadData();
}

// 获取状态标签类型
function getStatusTagType(status: string) {
  const statusMap: Record<string, string> = {
    'active': 'success',
    'inactive': 'default',
    'suspended': 'warning',
  };
  return statusMap[status] || 'default';
}

// 获取状态文本
function getStatusText(status: string) {
  const statusTextMap: Record<string, string> = {
    'active': '正常',
    'inactive': '停用',
    'suspended': '暂停',
  };
  return statusTextMap[status] || status;
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="h-full flex flex-col p-4">
    <div class="mb-4 flex items-center justify-between flex-shrink-0">
      <div>
        <Button type="primary" @click="handleCreate">
          <template #icon>
            <span class="i-ant-design:plus-outlined"></span>
          </template>
          新增采购主体
        </Button>
      </div>
      <div class="text-text-secondary text-sm">
        采购主体管理 - 管理公司基础信息、银行账户、跨境资质等
      </div>
    </div>
    
    <div class="flex-1 overflow-hidden">
    <Grid>
        <!-- 公司名称自定义渲染 -->
        <template #company_name="{ row }">
          <div class="flex items-center flex-wrap py-1">
            <span class="font-medium text-text whitespace-nowrap">{{ row.legal_name }}</span>
            <template v-if="row.english_name">
              <span class="text-text-secondary mx-2">/</span>
              <span class="text-text-secondary">
                {{ row.english_name }}
              </span>
            </template>
          </div>
        </template>

        <!-- 状态列自定义渲染 -->
        <template #status="{ row }">
          <Tag :color="getStatusTagType(row.status)">
            {{ getStatusText(row.status) }}
          </Tag>
        </template>
        
        <!-- 操作列 -->
      <template #action="{ row }">
          <div class="flex items-center justify-center gap-2">
            <Button type="link" size="small" @click="handleEdit(row)">
              编辑
            </Button>
            <Popconfirm 
              title="确认删除该采购主体吗？" 
              ok-text="确认"
              cancel-text="取消"
              @confirm="handleDelete(row)"
            >
              <Button type="link" size="small" danger>
                删除
              </Button>
        </Popconfirm>
          </div>
      </template>
    </Grid>
    </div>
    
    <Modal @success="handleSuccess" />
  </div>
</template>

<style scoped>
/* 确保表格容器占满剩余空间 */
:deep(.vxe-table--render-default) {
  height: 100%;
}
</style>
