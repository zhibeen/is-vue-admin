<script setup lang="ts">
/**
 * 发货单列表页面
 * 功能：展示发货单列表，支持搜索、筛选、查看详情
 */
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { 
  Form, 
  FormItem, 
  Input, 
  Select, 
  SelectOption, 
  DatePicker, 
  Button, 
  Space, 
  Tag,
  message 
} from 'ant-design-vue';

const RangePicker = DatePicker.RangePicker;
import { h, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { getShipmentList } from '#/api/logistics/shipment';

const router = useRouter();

// 状态标签颜色映射
const statusColorMap: Record<string, string> = {
  draft: 'default',
  confirmed: 'processing',
  shipped: 'success',
  cancelled: 'error',
};

// 状态文本映射
const statusTextMap: Record<string, string> = {
  draft: '草稿',
  confirmed: '已确认',
  shipped: '已发货',
  cancelled: '已取消',
};

// 来源文本映射
const sourceTextMap: Record<string, string> = {
  manual: '手工录入',
  excel: 'Excel导入',
  lingxing: '领星同步',
  yicang: '易仓同步',
};

// 搜索条件
const searchForm = ref({
  q: '',
  status: undefined as string | undefined,
  source: undefined as string | undefined,
  date_range: undefined as [string, string] | undefined,
});

// 分页状态
const pagination = ref({
  currentPage: 1,
  pageSize: 20,
  total: 0,
});

// Grid配置
const gridOptions: VxeGridProps = {
  columns: [
    {
      type: 'seq',
      width: 60,
      fixed: 'left',
    },
    {
      field: 'shipment_no',
      title: '发货单号',
      width: 180,
      fixed: 'left',
      slots: {
        default: ({ row }) => {
          return h(
            'a',
            {
              class: 'text-primary cursor-pointer',
              onClick: () => handleViewDetail(row.id),
            },
            row.shipment_no,
          );
        },
      },
    },
    {
      field: 'status',
      title: '单据状态',
      width: 100,
      slots: {
        default: ({ row }) => {
          return h(Tag, {
            color: statusColorMap[row.status] || 'default',
          }, () => statusTextMap[row.status] || row.status);
        },
      },
    },
    {
      field: 'source',
      title: '来源',
      width: 120,
      slots: {
        default: ({ row }) => {
          return sourceTextMap[row.source] || row.source || '-';
        },
      },
    },
    {
      field: 'consignee_name',
      title: '收货人',
      width: 180,
    },
    {
      field: 'consignee_country',
      title: '收货国家',
      width: 100,
    },
    {
      field: 'logistics_provider',
      title: '物流商',
      width: 150,
    },
    {
      field: 'tracking_no',
      title: '物流单号',
      width: 180,
    },
    {
      field: 'total_packages',
      title: '总件数',
      width: 100,
      align: 'right',
    },
    {
      field: 'total_amount',
      title: '总金额',
      width: 120,
      align: 'right',
      slots: {
        default: ({ row }) => {
          if (!row.total_amount) return '-';
          return h('span', `${row.currency || ''} ${Number(row.total_amount).toFixed(2)}`);
        },
      },
    },
    {
      field: 'is_declared',
      title: '报关',
      width: 80,
      align: 'center',
      slots: {
        default: ({ row }) => {
          return h(Tag, {
            color: row.is_declared ? 'success' : 'default',
          }, () => row.is_declared ? '已报' : '未报');
        },
      },
    },
    {
      field: 'is_contracted',
      title: '合同',
      width: 80,
      align: 'center',
      slots: {
        default: ({ row }) => {
          return h(Tag, {
            color: row.is_contracted ? 'success' : 'default',
          }, () => row.is_contracted ? '已生成' : '未生成');
        },
      },
    },
    {
      field: 'created_at',
      title: '创建时间',
      width: 160,
      sortable: true,
    },
    {
      field: 'action',
      title: '操作',
      width: 200,
      fixed: 'right',
      slots: {
        default: ({ row }) => {
          return h(Space, {}, () => [
            h(
              Button,
              {
                type: 'link',
                size: 'small',
                onClick: () => handleViewDetail(row.id),
              },
              () => '查看',
            ),
            row.status === 'draft' && h(
              Button,
              {
                type: 'link',
                size: 'small',
                onClick: () => handleEdit(row.id),
              },
              () => '编辑',
            ),
            row.status === 'draft' && h(
              Button,
              {
                type: 'link',
                size: 'small',
                onClick: () => handleConfirm(row.id),
              },
              () => '确认',
            ),
            row.status === 'confirmed' && !row.is_contracted && h(
              Button,
              {
                type: 'link',
                size: 'small',
                onClick: () => handleGenerateContracts(row.id),
              },
              () => '生成合同',
            ),
          ]);
        },
      },
    },
  ],
  data: [],
  pagerConfig: {
    enabled: true,
    currentPage: 1,
    pageSize: 20,
  },
  toolbarConfig: {
    refresh: true,
    refreshOptions: { code: 'query' },
    custom: true,
    slots: {
      buttons: () => {
        return h(Space, {}, () => [
          h(
            Button,
            {
              type: 'primary',
              onClick: handleCreate,
            },
            () => '新建发货单',
          ),
        ]);
      },
    },
  },
  loading: false,
};

// 初始化Grid
const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions,
  gridEvents: {
    toolbarToolClick: ({ code }: { code: string }) => {
      if (code === 'query') {
        loadData();
      }
    },
    pageChange: ({ currentPage, pageSize }: { currentPage: number; pageSize: number }) => {
      // 更新分页状态
      pagination.value.currentPage = currentPage;
      pagination.value.pageSize = pageSize;
      loadData();
    },
  },
});

// 加载数据
async function loadData() {
  try {
    gridApi.setLoading(true);
    
    // 处理日期范围
    const { date_range, ...rest } = searchForm.value;
    const params: any = {
      page: pagination.value.currentPage,
      per_page: pagination.value.pageSize,
      ...rest,
    };
    
    if (date_range && date_range.length === 2) {
      params.start_date = date_range[0];
      params.end_date = date_range[1];
    }
    
    const res = await getShipmentList(params);
    
    // 更新分页状态
    pagination.value.total = res.total;
    pagination.value.currentPage = res.page;
    pagination.value.pageSize = res.per_page;
    
    // 更新表格数据和分页配置
    gridApi.setGridOptions({
      data: res.items || [],
      pagerConfig: {
        currentPage: res.page,
        pageSize: res.per_page,
        total: res.total,
      },
    });
  } catch (error: any) {
    message.error(error.message || '加载数据失败');
  } finally {
    gridApi.setLoading(false);
  }
}

// 搜索
function handleSearch() {
  // 重置到第一页
  pagination.value.currentPage = 1;
  loadData();
}

// 重置搜索
function handleReset() {
  searchForm.value = {
    q: '',
    status: undefined,
    source: undefined,
    date_range: undefined,
  };
  handleSearch();
}

// 查看详情
function handleViewDetail(id: number) {
  router.push(`/logistics/shipment/${id}`);
}

// 新建
function handleCreate() {
  router.push('/logistics/shipment/create');
}

// 编辑
function handleEdit(id: number) {
  router.push(`/logistics/shipment/${id}/edit`);
}

// 确认发货单
async function handleConfirm(_id: number) {
  try {
    // TODO: 调用确认接口
    message.success('确认成功');
    loadData();
  } catch (error: any) {
    message.error(error.message || '确认失败');
  }
}

// 生成交付合同
async function handleGenerateContracts(_id: number) {
  try {
    // TODO: 调用生成合同接口
    message.success('生成合同成功');
    loadData();
  } catch (error: any) {
    message.error(error.message || '生成合同失败');
  }
}

// 挂载时加载数据
onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="p-4">
    <!-- 搜索区域 -->
    <div class="mb-4 bg-white dark:bg-gray-800 p-4 rounded">
      <Form layout="inline" :model="searchForm">
        <FormItem label="关键词">
          <Input
            v-model:value="searchForm.q"
            placeholder="发货单号/收货人/物流单号"
            style="width: 240px"
            allow-clear
            @press-enter="handleSearch"
          />
        </FormItem>
        
        <FormItem label="状态">
          <Select
            v-model:value="searchForm.status"
            placeholder="请选择"
            style="width: 120px"
            allow-clear
          >
            <SelectOption value="draft">草稿</SelectOption>
            <SelectOption value="confirmed">已确认</SelectOption>
            <SelectOption value="shipped">已发货</SelectOption>
            <SelectOption value="cancelled">已取消</SelectOption>
          </Select>
        </FormItem>
        
        <FormItem label="来源">
          <Select
            v-model:value="searchForm.source"
            placeholder="请选择"
            style="width: 120px"
            allow-clear
          >
            <SelectOption value="manual">手工录入</SelectOption>
            <SelectOption value="excel">Excel导入</SelectOption>
            <SelectOption value="lingxing">领星同步</SelectOption>
            <SelectOption value="yicang">易仓同步</SelectOption>
          </Select>
        </FormItem>
        
        <FormItem label="创建日期">
          <RangePicker
            v-model:value="searchForm.date_range"
            style="width: 240px"
          />
        </FormItem>
        
        <FormItem>
          <Space>
            <Button type="primary" @click="handleSearch">
              查询
            </Button>
            <Button @click="handleReset">
              重置
            </Button>
          </Space>
        </FormItem>
      </Form>
    </div>
    
    <!-- 表格 -->
    <Grid />
  </div>
</template>

<style scoped>
:deep(.vxe-table--render-default .vxe-body--row.row--hover) {
  background-color: #f5f5f5;
}

:deep(.dark .vxe-table--render-default .vxe-body--row.row--hover) {
  background-color: #1f1f1f;
}
</style>
