<script setup lang="ts">
import { useVbenDrawer } from '@vben/common-ui';
import { ref } from 'vue';
import { Descriptions, Table, Tag, Divider } from 'ant-design-vue';
import type { DeliveryContractDetail } from '#/api/serc/model';

const data = ref<DeliveryContractDetail | null>(null);

const [Drawer, drawerApi] = useVbenDrawer({
  title: '合同详情',
  class: 'w-[800px]',
  onOpenChange(isOpen) {
    if (isOpen) {
      const { row } = drawerApi.getData<any>();
      data.value = row;
    }
  },
});

const columns = [
  { title: '商品名称', dataIndex: 'product_name', key: 'product_name' },
  { title: '数量', dataIndex: 'confirmed_qty', key: 'confirmed_qty', align: 'right' },
  { title: '单价', dataIndex: 'unit_price', key: 'unit_price', align: 'right', customRender: ({ text }: any) => `￥${Number(text).toFixed(2)}` },
  { title: '总价', key: 'total_price', align: 'right', customRender: ({ record }: any) => `￥${(record.confirmed_qty * record.unit_price).toFixed(2)}` },
  { title: '备注', dataIndex: 'notes', key: 'notes' },
];
</script>

<template>
  <Drawer>
    <div v-if="data" class="p-4">
      <!-- Basic Info -->
      <Descriptions title="基本信息" bordered :column="2" size="small">
        <Descriptions.Item label="合同编号">{{ data.contract_no }}</Descriptions.Item>
        <Descriptions.Item label="状态">
            <Tag v-if="data.status === 'pending'" color="orange">待处理</Tag>
            <Tag v-else-if="data.status === 'settling'" color="blue">结算中</Tag>
            <Tag v-else-if="data.status === 'settled'" color="green">已结算</Tag>
            <Tag v-else>{{ data.status }}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="采购主体">{{ data.company_name || '-' }}</Descriptions.Item>
        <Descriptions.Item label="供应商">{{ data.supplier_name || '-' }}</Descriptions.Item>
        <Descriptions.Item label="业务日期">{{ (data as any).event_date || '-' }}</Descriptions.Item>
        <Descriptions.Item label="创建日期">{{ data.created_at }}</Descriptions.Item>
        
        <!-- New Fields -->
        <Descriptions.Item label="送货日期">{{ data.delivery_date || '-' }}</Descriptions.Item>
        <Descriptions.Item label="交付地点">{{ data.delivery_address || '-' }}</Descriptions.Item>
        
        <Descriptions.Item label="合同总额">
            <span class="text-lg font-bold text-primary">￥{{ Number(data.total_amount).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
        </Descriptions.Item>
        <Descriptions.Item label="已付金额">
            <span class="text-gray-500">￥{{ Number(data.paid_amount).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
        </Descriptions.Item>

        <Descriptions.Item label="合同备注" :span="2">{{ data.notes || '-' }}</Descriptions.Item>
      </Descriptions>

      <Divider />

      <!-- Items -->
      <div class="mb-2 font-bold">商品明细</div>
      <Table
        :columns="columns"
        :data-source="data.items"
        size="small"
        :pagination="false"
        bordered
        row-key="product_id"
      />
    </div>
  </Drawer>
</template>
