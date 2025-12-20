<template>
  <div class="p-4">
    <!-- 搜索栏 -->
    <Card class="mb-4">
      <Form layout="inline" class="gap-4">
        <FormItem label="物流服务商">
          <Select
            v-model:value="searchParams.logistics_provider_id"
            placeholder="请选择物流服务商"
            allow-clear
            class="!w-[200px]"
            @change="handleSearch"
          >
            <SelectOption
              v-for="provider in providerList"
              :key="provider.id"
              :value="provider.id"
            >
              {{ provider.provider_name }}
            </SelectOption>
          </Select>
        </FormItem>

        <FormItem label="状态">
          <Select
            v-model:value="searchParams.status"
            placeholder="请选择状态"
            allow-clear
            class="!w-[150px]"
            @change="handleSearch"
          >
            <SelectOption value="draft">草稿</SelectOption>
            <SelectOption value="confirmed">已确认</SelectOption>
            <SelectOption value="submitted">已提交</SelectOption>
            <SelectOption value="approved">已批准</SelectOption>
            <SelectOption value="paid">已付款</SelectOption>
          </Select>
        </FormItem>

        <FormItem label="对账周期">
          <RangePicker
            v-model:value="dateRange"
            format="YYYY-MM-DD"
            class="!w-[250px]"
            @change="handleDateChange"
          />
        </FormItem>

        <FormItem>
          <Space>
            <Button type="primary" @click="handleSearch">
              <template #icon>
                <SearchOutlined />
              </template>
              查询
            </Button>
            <Button @click="handleReset">重置</Button>
          </Space>
        </FormItem>
      </Form>
    </Card>

    <!-- 数据表格 -->
    <Card>
      <template #title>
        <div class="flex items-center justify-between">
          <span>物流对账单列表</span>
          <Button type="primary" @click="handleCreate">
            <template #icon>
              <PlusOutlined />
            </template>
            新建对账单
          </Button>
        </div>
      </template>

      <Grid />
    </Card>

    <!-- 创建/编辑对账单弹窗 -->
    <Modal
      v-model:open="modalVisible"
      :title="modalTitle"
      width="600px"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <Form
        ref="formRef"
        :model="formData"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <FormItem
          label="物流服务商"
          name="logistics_provider_id"
          :rules="[{ required: true, message: '请选择物流服务商' }]"
        >
          <Select
            v-model:value="formData.logistics_provider_id"
            placeholder="请选择物流服务商"
          >
            <SelectOption
              v-for="provider in providerList"
              :key="provider.id"
              :value="provider.id"
            >
              {{ provider.provider_name }}
            </SelectOption>
          </Select>
        </FormItem>

        <FormItem
          label="对账周期"
          name="period"
          :rules="[{ required: true, message: '请选择对账周期' }]"
        >
          <RangePicker
            v-model:value="formData.period"
            format="YYYY-MM-DD"
            class="w-full"
          />
        </FormItem>

        <FormItem label="自动包含服务" name="auto_include_services">
          <Switch v-model:checked="formData.auto_include_services" />
          <span class="ml-2 text-gray-500 text-sm">
            自动包含该周期内已确认的物流服务
          </span>
        </FormItem>

        <FormItem label="备注" name="notes">
          <Textarea
            v-model:value="formData.notes"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </FormItem>
      </Form>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue';
import { useRouter } from 'vue-router';
import {
  Card,
  Form,
  FormItem,
  Input,
  Select,
  SelectOption,
  Button,
  Space,
  DatePicker,
  Modal,
  Switch,
  Textarea,
  message,
} from 'ant-design-vue';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import {
  getStatementListApi,
  createStatementApi,
  confirmStatementApi,
  submitStatementToFinanceApi,
  deleteStatementApi,
  type LogisticsStatement,
  type StatementQueryParams,
} from '#/api/logistics/statement';
import { getProviderListApi, type LogisticsProvider } from '#/api/logistics/provider';

const { RangePicker } = DatePicker;
const router = useRouter();

// 状态数据
const providerList = ref<LogisticsProvider[]>([]);
const dateRange = ref<[string, string] | null>(null);
const searchParams = reactive<StatementQueryParams>({
  page: 1,
  per_page: 20,
});

// 表格配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'statement_no', title: '对账单号', width: 160 },
    {
      field: 'logistics_provider',
      title: '物流服务商',
      minWidth: 150,
      slots: { default: 'provider_default' },
    },
    {
      field: 'statement_period_start',
      title: '对账周期',
      width: 200,
      slots: { default: 'period_default' },
    },
    {
      field: 'total_amount',
      title: '总金额',
      width: 120,
      align: 'right',
      slots: { default: 'amount_default' },
    },
    {
      field: 'status',
      title: '状态',
      width: 100,
      slots: { default: 'status_default' },
    },
    {
      field: 'confirmed_at',
      title: '确认时间',
      width: 160,
    },
    {
      field: 'created_at',
      title: '创建时间',
      width: 160,
    },
    {
      title: '操作',
      width: 280,
      fixed: 'right',
      slots: { default: 'action_default' },
    },
  ],
  data: [],
  pagerConfig: {
    enabled: true,
  },
  toolbarConfig: {
    refresh: true,
    refreshOptions: { code: 'query' },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions,
  gridEvents: {
    toolbarToolClick: (params) => {
      if (params.code === 'query') {
        loadData();
      }
    },
  },
  gridSlots: {
    provider_default: ({ row }) => {
      return row.logistics_provider?.provider_name || '-';
    },
    period_default: ({ row }) => {
      return `${row.statement_period_start} ~ ${row.statement_period_end}`;
    },
    amount_default: ({ row }) => {
      return `¥${Number(row.total_amount).toFixed(2)}`;
    },
    status_default: ({ row }) => {
      const statusMap: Record<string, { color: string; text: string }> = {
        draft: { color: 'default', text: '草稿' },
        confirmed: { color: 'processing', text: '已确认' },
        submitted: { color: 'warning', text: '已提交' },
        approved: { color: 'success', text: '已批准' },
        paid: { color: 'success', text: '已付款' },
      };
      const config = statusMap[row.status] || { color: 'default', text: row.status };
      return h('a-tag', { color: config.color }, () => config.text);
    },
    action_default: ({ row }) => {
      return h(
        Space,
        {},
        {
          default: () => [
            h(
              Button,
              {
                type: 'link',
                size: 'small',
                onClick: () => handleView(row.id),
              },
              () => '查看',
            ),
            row.status === 'draft' &&
              h(
                Button,
                {
                  type: 'link',
                  size: 'small',
                  onClick: () => handleConfirm(row.id),
                },
                () => '确认',
              ),
            row.status === 'confirmed' &&
              h(
                Button,
                {
                  type: 'link',
                  size: 'small',
                  onClick: () => handleSubmit(row.id),
                },
                () => '提交财务',
              ),
            row.status === 'draft' &&
              h(
                Button,
                {
                  type: 'link',
                  size: 'small',
                  danger: true,
                  onClick: () => handleDelete(row.id),
                },
                () => '删除',
              ),
          ],
        },
      );
    },
  },
});

// 弹窗相关
const modalVisible = ref(false);
const modalTitle = ref('新建对账单');
const formRef = ref();
const formData = reactive({
  logistics_provider_id: undefined,
  period: null as [string, string] | null,
  auto_include_services: true,
  notes: '',
});

// 加载数据
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getStatementListApi(searchParams);
    gridApi.setGridOptions({ data: res || [] });
  } catch (error) {
    message.error('加载数据失败');
    console.error(error);
  } finally {
    gridApi.setLoading(false);
  }
}

// 加载物流服务商列表
async function loadProviders() {
  try {
    const res = await getProviderListApi({ is_active: true });
    providerList.value = res || [];
  } catch (error) {
    console.error('加载物流服务商失败:', error);
  }
}

// 搜索
function handleSearch() {
  searchParams.page = 1;
  loadData();
}

// 重置
function handleReset() {
  searchParams.logistics_provider_id = undefined;
  searchParams.status = undefined;
  searchParams.statement_period_start = undefined;
  searchParams.statement_period_end = undefined;
  dateRange.value = null;
  handleSearch();
}

// 日期范围变化
function handleDateChange(dates: [string, string] | null) {
  if (dates && dates.length === 2) {
    searchParams.statement_period_start = dates[0];
    searchParams.statement_period_end = dates[1];
  } else {
    searchParams.statement_period_start = undefined;
    searchParams.statement_period_end = undefined;
  }
}

// 新建对账单
function handleCreate() {
  modalTitle.value = '新建对账单';
  modalVisible.value = true;
  formData.logistics_provider_id = undefined;
  formData.period = null;
  formData.auto_include_services = true;
  formData.notes = '';
}

// 弹窗确认
async function handleModalOk() {
  try {
    await formRef.value?.validate();
    
    const data = {
      logistics_provider_id: formData.logistics_provider_id!,
      statement_period_start: formData.period![0],
      statement_period_end: formData.period![1],
      auto_include_services: formData.auto_include_services,
      notes: formData.notes,
    };

    await createStatementApi(data);
    message.success('创建成功');
    modalVisible.value = false;
    loadData();
  } catch (error: any) {
    if (error.errorFields) {
      return; // 表单验证错误
    }
    message.error(error.message || '创建失败');
    console.error(error);
  }
}

// 弹窗取消
function handleModalCancel() {
  modalVisible.value = false;
  formRef.value?.resetFields();
}

// 查看详情
function handleView(id: number) {
  router.push(`/logistics/statement/${id}`);
}

// 确认对账单
async function handleConfirm(id: number) {
  Modal.confirm({
    title: '确认对账单',
    content: '确认后对账单将锁定，无法再修改。是否继续？',
    async onOk() {
      try {
        await confirmStatementApi(id);
        message.success('确认成功');
        loadData();
      } catch (error: any) {
        message.error(error.message || '确认失败');
        console.error(error);
      }
    },
  });
}

// 提交财务
async function handleSubmit(id: number) {
  Modal.confirm({
    title: '提交财务',
    content: '提交后将生成财务应付单，是否继续？',
    async onOk() {
      try {
        await submitStatementToFinanceApi(id);
        message.success('提交成功');
        loadData();
      } catch (error: any) {
        message.error(error.message || '提交失败');
        console.error(error);
      }
    },
  });
}

// 删除
async function handleDelete(id: number) {
  Modal.confirm({
    title: '删除对账单',
    content: '确定要删除该对账单吗？此操作不可恢复。',
    okType: 'danger',
    async onOk() {
      try {
        await deleteStatementApi(id);
        message.success('删除成功');
        loadData();
      } catch (error: any) {
        message.error(error.message || '删除失败');
        console.error(error);
      }
    },
  });
}

onMounted(() => {
  loadProviders();
  loadData();
});
</script>

<style scoped>
:deep(.ant-form-inline .ant-form-item) {
  margin-right: 16px;
  margin-bottom: 0;
}
</style>

