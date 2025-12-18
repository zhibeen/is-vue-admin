<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getPaymentPool, createPayment } from '#/api/serc/finance';
import { message, Modal, Input, Button, Tag, Select } from 'ant-design-vue';
import { onMounted, ref } from 'vue';
import { Page } from '@vben/common-ui';

const gridOptions: VxeGridProps = {
  columns: [
    { type: 'checkbox', width: 50, fixed: 'left' },
    { field: 'soa_no', title: '结算单号', minWidth: 180 },
    { field: 'amount', title: '应付金额', minWidth: 120, formatter: 'formatMoney', align: 'right' },
    { field: 'type', title: '款项类型', width: 100, slots: { default: 'type_default' } },
    { field: 'due_date', title: '预计付款日', width: 120 },
    { field: 'priority', title: '优先级', width: 80, align: 'center' },
    { field: 'status', title: '状态', width: 120, slots: { default: 'status_default' } },
  ],
  proxyConfig: {
    ajax: {
      query: async () => {
        const res = await getPaymentPool();
        // Handle API wrapper if needed, similar to other views
        const list = Array.isArray(res) ? res : (res as any).data || [];
        return {
          items: list,
          total: list.length, 
        };
      },
    },
  },
  pagerConfig: {
    enabled: false, // Pool items usually aren't paginated in huge numbers, or backend doesn't support pagination yet
  },
  toolbarConfig: {
    custom: true,
    refresh: true,
    zoom: true,
    slots: { buttons: 'toolbar_buttons' },
  },
  height: 'auto',
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

// --- Payment Modal ---
const paymentModalVisible = ref(false);
const paymentLoading = ref(false);
const bankAccount = ref('BANK-DEFAULT-01'); // Default
const selectedIds = ref<number[]>([]);

// Mock Bank Accounts
const bankAccounts = [
    { value: 'BANK-DEFAULT-01', label: '主要基本户 (CNY)' },
    { value: 'BANK-USD-01', label: '美元外汇户 (USD)' },
];

function handleOpenPaymentModal() {
  const records = gridApi.grid.getCheckboxRecords();
  if (!records || records.length === 0) {
    message.warning('请先勾选待付项');
    return;
  }
  selectedIds.value = records.map((row: any) => row.id);
  paymentModalVisible.value = true;
}

async function handleConfirmPayment() {
    if (!bankAccount.value) {
        message.error('请选择付款账号');
        return;
    }
    
    try {
        paymentLoading.value = true;
        await createPayment({
            pool_item_ids: selectedIds.value,
            bank_account: bankAccount.value
        });
        message.success('付款单 (L3) 已生成');
        paymentModalVisible.value = false;
        gridApi.reload();
    } catch (e) {
        console.error(e);
        // message handled by interceptor or default
    } finally {
        paymentLoading.value = false;
    }
}

onMounted(() => {
  // gridApi.query();
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar_buttons>
        <Button type="primary" @click="handleOpenPaymentModal">
          合并支付 (生成L3)
        </Button>
      </template>

      <template #type_default="{ row }">
          <Tag v-if="row.type === 'goods'" color="blue">货款</Tag>
          <Tag v-else-if="row.type === 'deposit'" color="cyan">定金</Tag>
          <Tag v-else-if="row.type === 'tax'" color="purple">税款</Tag>
          <Tag v-else>{{ row.type }}</Tag>
      </template>

      <template #status_default="{ row }">
          <Tag v-if="row.status === 'pending_approval'" color="orange">待审批</Tag>
          <Tag v-else-if="row.status === 'pending_payment'" color="blue">待支付</Tag>
          <Tag v-else-if="row.status === 'paid'" color="green">已支付</Tag>
          <Tag v-else>{{ row.status }}</Tag>
      </template>
    </Grid>

    <Modal
        v-model:open="paymentModalVisible"
        title="生成付款申请单"
        @ok="handleConfirmPayment"
        :confirmLoading="paymentLoading"
    >
        <div class="p-4 space-y-4">
            <div>
                <span class="font-bold">已选笔数:</span> {{ selectedIds.length }} 笔
            </div>
            <div>
                <div class="mb-2">付款账号:</div>
                <Select 
                    v-model:value="bankAccount" 
                    :options="bankAccounts"
                    style="width: 100%"
                />
            </div>
        </div>
    </Modal>
  </Page>
</template>
