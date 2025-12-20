<script setup lang="ts">
/**
 * 发货单详情 - 商品明细Tab
 */
import { Table, Row, Col } from 'ant-design-vue';
import { InboxOutlined } from '@ant-design/icons-vue';
import { computed } from 'vue';
import type { Shipment, ShipmentItem } from '#/api/logistics/shipment';
import type { PurchaseItem } from '#/api/logistics/purchase-item';

interface Props {
  shipment: Shipment | null;
  purchaseItems: PurchaseItem[];
}

const props = defineProps<Props>();

// 计算总数量
const totalQuantity = computed(() => {
  if (!props.shipment?.items) return 0;
  return props.shipment.items.reduce((sum, item) => sum + item.quantity, 0);
});

// 商品明细表格列定义
const columns = [
  {
    title: '序号',
    width: 60,
    customRender: ({ index }: { index: number }) => index + 1,
  },
  {
    title: 'SKU',
    dataIndex: 'sku',
    key: 'sku',
    width: 150,
  },
  {
    title: '品名',
    dataIndex: 'product_name',
    key: 'product_name',
    width: 200,
  },
  {
    title: '出口申报名称',
    dataIndex: 'export_name',
    key: 'export_name',
    width: 150,
  },
  {
    title: 'HS CODE',
    dataIndex: 'hs_code',
    key: 'hs_code',
    width: 120,
  },
  {
    title: '数量',
    dataIndex: 'quantity',
    key: 'quantity',
    width: 100,
    align: 'right' as const,
  },
  {
    title: '申报单位',
    dataIndex: 'customs_unit',
    key: 'customs_unit',
    width: 90,
  },
  {
    title: '采购来源',
    dataIndex: 'supplier_name',
    key: 'purchase_sources',
    width: 220,
    customRender: ({ record }: any) => {
      // 根据SKU查找对应的采购明细
      const sku = record.sku;
      const purchasesForSku = props.purchaseItems.filter((p: any) => p.sku === sku);
      
      if (purchasesForSku.length === 0) {
        return record.supplier_name || '-';
      }
      
      // 构建采购来源信息：PO号(数量) | PO号(数量)
      const sources = purchasesForSku.map((p: any) => {
        const poNo = p.purchase_order_no || '未关联';
        return `${poNo}(${p.quantity})`;
      });
      
      const sourceText = sources.join(' | ');
      const supplierText = record.supplier_name ? `${record.supplier_name} - ` : '';
      
      return `${supplierText}${sourceText}`;
    },
  },
];
</script>

<template>
  <div>
    <Table
      :columns="columns"
      :data-source="shipment?.items || []"
      :pagination="false"
      :scroll="{ x: 1200 }"
      row-key="id"
      bordered
      size="middle"
    />
    
    <!-- 合计信息 -->
    <div v-if="shipment?.items && shipment.items.length > 0" 
         class="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
      <Row :gutter="24">
        <Col :xs="24" :sm="12">
          <div class="flex items-center justify-center gap-2">
            <span class="text-sm text-gray-600 dark:text-gray-400">商品种类：</span>
            <span class="text-base font-medium">{{ shipment.items.length }} SKU</span>
          </div>
        </Col>
        <Col :xs="24" :sm="12">
          <div class="flex items-center justify-center gap-2">
            <span class="text-sm text-gray-600 dark:text-gray-400">总数量：</span>
            <span class="text-base font-medium">{{ totalQuantity }} 件</span>
          </div>
        </Col>
      </Row>
    </div>
  </div>
</template>

