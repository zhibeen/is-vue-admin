<script setup lang="ts">
import { useVbenDrawer } from '@vben/common-ui';
import { Descriptions, Table, Tag } from 'ant-design-vue';
import { ref } from 'vue';
import type { SOAItem } from '#/api/serc/model';

const data = ref<SOAItem | null>(null);

const [DrawerComponent, drawerApi] = useVbenDrawer({
  title: '结算单详情',
  size: 'large',
  onOpenChange: (isOpen) => {
    if (isOpen) {
      const { row } = drawerApi.getData();
      data.value = row;
    } else {
        data.value = null;
    }
  },
});

const columns = [
    { title: 'L1 合同号', dataIndex: 'l1_contract_no' },
    { title: '对账金额', dataIndex: 'amount', customRender: ({ text }: any) => `￥${Number(text).toFixed(2)}` },
];
</script>

<template>
  <DrawerComponent>
    <div v-if="data" class="p-4 space-y-6">
        <Descriptions title="基本信息" bordered size="small" :column="2">
            <Descriptions.Item label="结算单号">{{ data.soa_no }}</Descriptions.Item>
            <Descriptions.Item label="供应商">{{ data.supplier_name }}</Descriptions.Item>
            <Descriptions.Item label="应付总额">
                <span class="font-bold text-lg">￥{{ Number(data.total_payable).toLocaleString() }}</span>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
                <Tag v-if="data.status === 'draft'" color="orange">草稿</Tag>
                <Tag v-else-if="data.status === 'confirmed'" color="green">已确认</Tag>
                <Tag v-else>{{ data.status }}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="资金状态">{{ data.payment_status }}</Descriptions.Item>
            <Descriptions.Item label="票据状态">{{ data.invoice_status }}</Descriptions.Item>
        </Descriptions>

        <div>
            <h3 class="font-bold mb-2">包含的交付合同 (L1)</h3>
            <Table 
                :dataSource="data.details || []" 
                :columns="columns" 
                size="small" 
                bordered 
                :pagination="false"
            />
        </div>
    </div>
  </DrawerComponent>
</template>

