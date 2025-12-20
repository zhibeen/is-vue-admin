<script setup lang="ts">
/**
 * 发货单详情 - 采购明细Tab
 */
import { Alert, Button, Space, Table } from 'ant-design-vue';
import { DollarOutlined, UploadOutlined } from '@ant-design/icons-vue';
import type { PurchaseItem } from '#/api/logistics/purchase-item';
import type { Shipment } from '#/api/logistics/shipment';

interface Props {
  shipment: Shipment | null;
  purchaseItems: PurchaseItem[];
  loading: boolean;
}

interface Emits {
  (e: 'add'): void;
  (e: 'import'): void;
  (e: 'recalculate'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 采购明细表格列定义
const columns = [
  { title: '采购单号', dataIndex: 'purchase_order_no', key: 'purchase_order_no', width: 150 },
  { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 120 },
  { title: '品名', dataIndex: 'product_name', key: 'product_name', width: 200 },
  { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 100, align: 'right' as const },
  { title: '采购单价', dataIndex: 'purchase_unit_price', key: 'purchase_unit_price', width: 120, align: 'right' as const },
  { title: '采购金额', dataIndex: 'purchase_total_price', key: 'purchase_total_price', width: 120, align: 'right' as const },
  { title: '供应商', dataIndex: 'supplier_name', key: 'supplier_name', width: 150 },
  { title: '批次号', dataIndex: 'batch_no', key: 'batch_no', width: 120 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' as const },
];
</script>

<template>
  <div>
    <Alert 
      type="info" 
      show-icon 
      class="mb-4"
      message="采购明细是唯一的价格数据源，商品明细通过采购明细自动汇总生成"
    />
    
    <div class="mb-4">
      <Space>
        <Button type="primary" @click="emit('add')">
          添加采购明细
        </Button>
        <Button @click="emit('import')">
          <UploadOutlined />
          批量导入
        </Button>
        <Button @click="emit('recalculate')">
          重新计算商品明细
        </Button>
      </Space>
    </div>
    
    <Table
      :columns="columns"
      :data-source="purchaseItems"
      :loading="loading"
      :pagination="false"
      :scroll="{ x: 1400 }"
      row-key="id"
      bordered
      size="middle"
    >
      <template #emptyText>
        <div class="text-center py-8">
          <p class="text-gray-400 mb-4">暂无采购明细</p>
          <Button type="primary" @click="emit('add')">添加采购明细</Button>
        </div>
      </template>
    </Table>
    
    <div class="mt-4 text-right text-sm text-gray-500">
      💡 提示：修改采购明细后，商品明细将自动重新计算
    </div>
  </div>
</template>

