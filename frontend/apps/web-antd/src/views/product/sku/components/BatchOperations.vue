<script setup lang="ts">
import { ref, watch } from 'vue';
import { Button, Modal, message, Progress, Space } from 'ant-design-vue';
import { CheckOutlined, CloseOutlined, ExportOutlined } from '@ant-design/icons-vue';
import type { Sku } from '#/api/core/product';

const props = defineProps<{
  selectedRows: Sku[];
}>();

const emit = defineEmits<{
  (e: 'batch-enable'): void;
  (e: 'batch-disable'): void;
  (e: 'batch-export'): void;
  (e: 'clear-selection'): void;
}>();

const visible = ref(false);
const operationType = ref<'enable' | 'disable' | 'export' | null>(null);
const processing = ref(false);
const progress = ref(0);

// 统计信息
const stats = ref({
  total: 0,
  active: 0,
  inactive: 0,
  withStock: 0,
  withoutStock: 0,
});

// 更新统计信息
watch(() => props.selectedRows, (rows) => {
  stats.value = {
    total: rows.length,
    active: rows.filter(row => row.is_active).length,
    inactive: rows.filter(row => !row.is_active).length,
    withStock: rows.filter(row => (row.stock_quantity || 0) > 0).length,
    withoutStock: rows.filter(row => (row.stock_quantity || 0) === 0).length,
  };
}, { immediate: true });

// 批量启用
function handleBatchEnable() {
  if (props.selectedRows.length === 0) {
    message.warning('请先选择要操作的SKU');
    return;
  }
  
  operationType.value = 'enable';
  visible.value = true;
}

// 批量停用
function handleBatchDisable() {
  if (props.selectedRows.length === 0) {
    message.warning('请先选择要操作的SKU');
    return;
  }
  
  operationType.value = 'disable';
  visible.value = true;
}

// 批量导出
function handleBatchExport() {
  if (props.selectedRows.length === 0) {
    message.warning('请先选择要导出的SKU');
    return;
  }
  
  operationType.value = 'export';
  visible.value = true;
}

// 确认操作
async function handleConfirm() {
  if (!operationType.value) return;
  
  processing.value = true;
  progress.value = 0;
  
  try {
    // 模拟操作进度
    const interval = setInterval(() => {
      progress.value += 10;
      if (progress.value >= 100) {
        clearInterval(interval);
        
        // 根据操作类型执行不同的操作
        switch (operationType.value) {
          case 'enable':
            emit('batch-enable');
            message.success(`已成功启用 ${props.selectedRows.length} 个SKU`);
            break;
          case 'disable':
            emit('batch-disable');
            message.success(`已成功停用 ${props.selectedRows.length} 个SKU`);
            break;
          case 'export':
            emit('batch-export');
            message.success(`已成功导出 ${props.selectedRows.length} 个SKU`);
            break;
        }
        
        processing.value = false;
        visible.value = false;
        operationType.value = null;
        emit('clear-selection');
      }
    }, 100);
    
  } catch (error) {
    console.error('批量操作失败:', error);
    message.error('操作失败，请重试');
    processing.value = false;
  }
}

// 取消操作
function handleCancel() {
  if (!processing.value) {
    visible.value = false;
    operationType.value = null;
  }
}

// 获取操作标题
const operationTitle = {
  enable: '批量启用SKU',
  disable: '批量停用SKU',
  export: '批量导出SKU',
}[operationType.value || 'enable'];

// 获取操作描述
const operationDescription = {
  enable: `确定要启用选中的 ${props.selectedRows.length} 个SKU吗？`,
  disable: `确定要停用选中的 ${props.selectedRows.length} 个SKU吗？`,
  export: `确定要导出选中的 ${props.selectedRows.length} 个SKU吗？`,
}[operationType.value || 'enable'];
</script>

<template>
  <!-- 批量操作按钮组 -->
  <div v-if="props.selectedRows.length > 0" class="batch-operations">
    <div class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
      <div class="flex items-center justify-between">
        <div class="text-blue-700">
          <div class="font-bold">已选择 {{ stats.total }} 个SKU</div>
          <div class="text-sm text-gray-600 mt-1">
            <span>启用: {{ stats.active }} | 停用: {{ stats.inactive }} | 有库存: {{ stats.withStock }} | 无库存: {{ stats.withoutStock }}</span>
          </div>
        </div>
        <Space>
          <Button @click="handleBatchEnable" :disabled="stats.active === stats.total">
            <CheckOutlined /> 批量启用
          </Button>
          <Button @click="handleBatchDisable" :disabled="stats.inactive === stats.total">
            <CloseOutlined /> 批量停用
          </Button>
          <Button type="primary" @click="handleBatchExport">
            <ExportOutlined /> 导出选中
          </Button>
          <Button @click="$emit('clear-selection')">
            取消选择
          </Button>
        </Space>
      </div>
    </div>

    <!-- 操作确认模态框 -->
    <Modal
      v-model:open="visible"
      :title="operationTitle"
      :ok-text="processing ? '处理中...' : '确认'"
      :cancel-text="processing ? '取消' : '取消'"
      :ok-button-props="{ disabled: processing }"
      :cancel-button-props="{ disabled: processing }"
      @ok="handleConfirm"
      @cancel="handleCancel"
    >
      <div v-if="!processing">
        <p>{{ operationDescription }}</p>
        
        <!-- 操作详情 -->
        <div class="mt-4 p-3 bg-gray-50 rounded">
          <div class="text-sm text-gray-600 mb-2">操作详情:</div>
          <div class="space-y-1">
            <div v-for="(row, index) in props.selectedRows.slice(0, 5)" :key="row.sku" class="text-sm">
              {{ index + 1 }}. {{ row.sku }} - {{ row.product_name }}
            </div>
            <div v-if="props.selectedRows.length > 5" class="text-sm text-gray-500">
              等 {{ props.selectedRows.length - 5 }} 个SKU...
            </div>
          </div>
        </div>
      </div>
      
      <!-- 处理进度 -->
      <div v-else class="text-center py-4">
        <Progress :percent="progress" />
        <p class="mt-2 text-gray-600">正在处理中，请稍候...</p>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.batch-operations {
  transition: all 0.3s ease;
}
</style>
