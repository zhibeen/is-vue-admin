<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getPaymentPool, createPayment } from '#/api/serc/finance';
import { message } from 'ant-design-vue';
import { onMounted } from 'vue';

const gridOptions: VxeGridProps = {
  columns: [
    { type: 'checkbox', width: 50 },
    { field: 'soa_no', title: '结算单号', minWidth: 180 },
    { field: 'amount', title: '金额', minWidth: 120, formatter: 'formatMoney' },
    { field: 'type', title: '类型', width: 100 },
    { field: 'priority', title: '优先级', width: 80 },
    { field: 'status', title: '状态', width: 100 },
  ],
  proxyConfig: {
    ajax: {
      query: async () => {
        const res = await getPaymentPool();
        return {
          result: res,
          total: res.length, 
        };
      },
    },
  },
  pagerConfig: {
    enabled: false,
  },
  toolbarConfig: {
    refresh: true,
    zoom: true,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

onMounted(() => {
  gridApi.query();
});

async function handleBatchPay() {
  const records = gridApi.getCheckboxRecords();
  if (!records || records.length === 0) {
    message.warning('请先勾选待付项');
    return;
  }
  
  const ids = records.map(row => row.id);
  try {
    await createPayment({
      pool_item_ids: ids,
      bank_account: 'BANK-DEFAULT-01'
    });
    message.success('付款单已生成');
    gridApi.reload();
  } catch (e) {
    console.error(e);
  }
}
</script>

<template>
  <div class="p-4">
    <div class="mb-2">
      <a-button type="primary" @click="handleBatchPay">合并支付 (生成L3)</a-button>
    </div>
    <Grid />
  </div>
</template>
