<template>
  <div class="p-4">
    <!-- 搜索栏 -->
    <Card class="mb-4">
      <Form layout="inline" class="gap-4">
        <FormItem label="来源类型">
          <Select
            v-model:value="searchParams.source_type"
            placeholder="请选择来源类型"
            allow-clear
            class="!w-[150px]"
            @change="handleSearch"
          >
            <SelectOption value="logistics">物流对账</SelectOption>
            <SelectOption value="supply_contract">供货合同</SelectOption>
            <SelectOption value="expense">费用单</SelectOption>
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
            <SelectOption value="pending_approval">待审批</SelectOption>
            <SelectOption value="approved">已批准</SelectOption>
            <SelectOption value="in_pool">付款池中</SelectOption>
            <SelectOption value="paid">已付款</SelectOption>
          </Select>
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
    <Card title="财务应付单列表">
      <Grid />
    </Card>

    <!-- 付款弹窗 -->
    <Modal
      v-model:open="paymentModalVisible"
      title="标记为已付款"
      @ok="handlePaymentOk"
      @cancel="handlePaymentCancel"
    >
      <Form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <FormItem label="应付单号">
          {{ currentPayable?.payable_no }}
        </FormItem>
        <FormItem label="应付金额">
          ¥{{ Number(currentPayable?.amount || 0).toFixed(2) }}
        </FormItem>
        <FormItem label="实付金额">
          <InputNumber
            v-model:value="paidAmount"
            :min="0"
            :max="currentPayable?.amount"
            :precision="2"
            class="w-full"
            placeholder="请输入实付金额"
          />
        </FormItem>
      </Form>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue';
import {
  Card,
  Form,
  FormItem,
  Select,
  SelectOption,
  Button,
  Space,
  Modal,
  InputNumber,
  message,
} from 'ant-design-vue';
import { SearchOutlined } from '@ant-design/icons-vue';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import {
  getPayableListApi,
  approvePayableApi,
  addToPoolApi,
  markAsPaidApi,
  type FinPayable,
  type PayableQueryParams,
} from '#/api/finance/payable';

// 搜索参数
const searchParams = reactive<PayableQueryParams>({
  page: 1,
  per_page: 20,
});

// 表格配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'payable_no', title: '应付单号', width: 160 },
    {
      field: 'source_type',
      title: '来源类型',
      width: 120,
      slots: { default: 'source_type_default' },
    },
    { field: 'source_no', title: '来源单号', width: 160 },
    { field: 'supplier_name', title: '供应商', minWidth: 150 },
    {
      field: 'amount',
      title: '应付金额',
      width: 120,
      align: 'right',
      slots: { default: 'amount_default' },
    },
    { field: 'due_date', title: '应付日期', width: 120 },
    {
      field: 'status',
      title: '状态',
      width: 100,
      slots: { default: 'status_default' },
    },
    { field: 'created_at', title: '创建时间', width: 160 },
    {
      title: '操作',
      width: 240,
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
    source_type_default: ({ row }) => {
      const typeMap: Record<string, string> = {
        logistics: '物流对账',
        supply_contract: '供货合同',
        expense: '费用单',
      };
      return typeMap[row.source_type] || row.source_type;
    },
    amount_default: ({ row }) => {
      return `¥${Number(row.amount).toFixed(2)}`;
    },
    status_default: ({ row }) => {
      const statusMap: Record<string, { color: string; text: string }> = {
        pending_approval: { color: 'warning', text: '待审批' },
        approved: { color: 'processing', text: '已批准' },
        in_pool: { color: 'cyan', text: '付款池中' },
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
            row.status === 'pending_approval' &&
              h(
                Button,
                {
                  type: 'link',
                  size: 'small',
                  onClick: () => handleApprove(row.id),
                },
                () => '批准',
              ),
            row.status === 'approved' &&
              h(
                Button,
                {
                  type: 'link',
                  size: 'small',
                  onClick: () => handleAddToPool(row.id),
                },
                () => '加入付款池',
              ),
            (row.status === 'approved' || row.status === 'in_pool') &&
              h(
                Button,
                {
                  type: 'link',
                  size: 'small',
                  onClick: () => handlePay(row),
                },
                () => '标记已付款',
              ),
          ],
        },
      );
    },
  },
});

// 付款弹窗
const paymentModalVisible = ref(false);
const currentPayable = ref<FinPayable | null>(null);
const paidAmount = ref(0);

// 加载数据
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getPayableListApi(searchParams);
    gridApi.setGridOptions({ data: res || [] });
  } catch (error) {
    message.error('加载数据失败');
    console.error(error);
  } finally {
    gridApi.setLoading(false);
  }
}

// 搜索
function handleSearch() {
  searchParams.page = 1;
  loadData();
}

// 重置
function handleReset() {
  searchParams.source_type = undefined;
  searchParams.status = undefined;
  handleSearch();
}

// 批准
async function handleApprove(id: number) {
  Modal.confirm({
    title: '批准应付单',
    content: '批准后应付单将可以加入付款池，是否继续？',
    async onOk() {
      try {
        await approvePayableApi(id);
        message.success('批准成功');
        loadData();
      } catch (error: any) {
        message.error(error.message || '批准失败');
        console.error(error);
      }
    },
  });
}

// 加入付款池
async function handleAddToPool(id: number) {
  Modal.confirm({
    title: '加入付款池',
    content: '应付单将加入付款池，等待统一付款，是否继续？',
    async onOk() {
      try {
        await addToPoolApi(id);
        message.success('已加入付款池');
        loadData();
      } catch (error: any) {
        message.error(error.message || '操作失败');
        console.error(error);
      }
    },
  });
}

// 打开付款弹窗
function handlePay(payable: FinPayable) {
  currentPayable.value = payable;
  paidAmount.value = payable.amount;
  paymentModalVisible.value = true;
}

// 确认付款
async function handlePaymentOk() {
  if (!currentPayable.value) return;

  try {
    await markAsPaidApi(currentPayable.value.id, {
      paid_amount: paidAmount.value,
    });
    message.success('标记成功');
    paymentModalVisible.value = false;
    loadData();
  } catch (error: any) {
    message.error(error.message || '操作失败');
    console.error(error);
  }
}

// 取消付款
function handlePaymentCancel() {
  paymentModalVisible.value = false;
  currentPayable.value = null;
  paidAmount.value = 0;
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
:deep(.ant-form-inline .ant-form-item) {
  margin-right: 16px;
  margin-bottom: 0;
}
</style>

