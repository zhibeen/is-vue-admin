<script setup lang="ts">
/**
 * 发货单详情 - 顶部标题栏和进度条
 */
import { Card, Tag, Button, Space, Steps, Step, Alert, Row, Col, Statistic } from 'ant-design-vue';
import { computed } from 'vue';
import type { Shipment } from '#/api/logistics/shipment';

interface Props {
  shipment: Shipment | null;
  isEditing: boolean;
  saving: boolean;
}

interface Emits {
  (e: 'back'): void;
  (e: 'edit'): void;
  (e: 'save'): void;
  (e: 'cancelEdit'): void;
  (e: 'confirm'): void;
  (e: 'generateContracts'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 状态标签颜色
const statusColorMap: Record<string, string> = {
  draft: 'default',
  confirmed: 'processing',
  shipped: 'success',
  cancelled: 'error',
};

// 状态文本
const statusTextMap: Record<string, string> = {
  draft: '草稿',
  confirmed: '已确认',
  shipped: '已发货',
  cancelled: '已取消',
};

// 来源文本
const sourceTextMap: Record<string, string> = {
  manual: '手工录入',
  excel: 'Excel导入',
  lingxing: '领星同步',
  yicang: '易仓同步',
};

// 流程步骤映射
const statusStepMap: Record<string, number> = {
  draft: 0,
  confirmed: 1,
  shipped: 2,
  cancelled: 2,
};

// 计算总数量
const totalQuantity = computed(() => {
  if (!props.shipment?.items) return 0;
  return props.shipment.items.reduce((sum, item) => sum + item.quantity, 0);
});

// 计算待办事项
const todoItems = computed(() => {
  const todos: string[] = [];
  if (!props.shipment) return todos;
  
  if (props.shipment.status === 'draft') {
    todos.push('需要确认发货单');
  }
  if (props.shipment.status === 'confirmed' && !props.shipment.is_declared) {
    todos.push('需要生成报关单');
  }
  if (props.shipment.status === 'confirmed' && !props.shipment.is_contracted) {
    todos.push('需要生成交付合同');
  }
  
  return todos;
});
</script>

<template>
  <div class="bg-white dark:bg-gray-800 p-6 rounded border border-gray-200 dark:border-gray-700 mb-4">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <h1 class="text-2xl font-bold m-0">
          {{ shipment?.shipment_no || '加载中...' }}
        </h1>
        <Tag v-if="shipment" :color="statusColorMap[shipment.status || '']" class="text-base px-3 py-1">
          {{ statusTextMap[shipment.status || ''] || shipment.status }}
        </Tag>
        <Tag v-if="shipment?.source" color="blue" class="px-3 py-1">
          {{ sourceTextMap[shipment.source] || shipment.source }}
        </Tag>
      </div>
      
      <Space size="middle">
        <Button @click="emit('back')">返回列表</Button>
        
        <!-- 非编辑模式按钮 -->
        <template v-if="!isEditing">
          <Button v-if="shipment?.status === 'draft'" @click="emit('edit')">
            编辑
          </Button>
          <Button v-if="shipment?.status === 'draft'" type="primary" @click="emit('confirm')">
            确认发货单
          </Button>
          <Button
            v-if="shipment?.status === 'confirmed' && !shipment.is_contracted"
            type="primary"
            @click="emit('generateContracts')"
          >
            生成交付合同
          </Button>
        </template>
        
        <!-- 编辑模式按钮 -->
        <template v-else>
          <Button @click="emit('cancelEdit')">取消</Button>
          <Button type="primary" :loading="saving" @click="emit('save')">
            保存
          </Button>
        </template>
      </Space>
    </div>
    
    <!-- 流程进度条 -->
    <div class="p-5 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700 mb-4">
      <Steps :current="statusStepMap[shipment?.status || 'draft']" :status="shipment?.status === 'cancelled' ? 'error' : 'process'">
        <Step title="创建发货单" :description="shipment?.created_at" />
        <Step title="确认发货" :description="shipment?.status === 'confirmed' ? '已确认' : '待确认'" />
        <Step title="发货中" :description="shipment?.actual_ship_date || '待发货'" />
      </Steps>
    </div>
    
    <!-- 待办事项提醒 -->
    <Alert
      v-if="todoItems.length > 0"
      type="warning"
      show-icon
      class="mb-4"
    >
      <template #message>
        <div class="flex items-center gap-2">
          <span class="font-semibold">待办事项：</span>
          <span v-for="(todo, index) in todoItems" :key="index">
            {{ todo }}<span v-if="index < todoItems.length - 1">；</span>
          </span>
        </div>
      </template>
    </Alert>
    
    <!-- 关键指标卡片 -->
    <Row :gutter="16" class="mt-4">
      <Col :xs="24" :sm="12" :md="8">
        <Card :bordered="true">
          <Statistic
            title="商品数量"
            :value="totalQuantity"
            suffix="件"
          />
        </Card>
      </Col>
      <Col :xs="24" :sm="12" :md="8">
        <Card :bordered="true">
          <Statistic
            title="总重量"
            :value="shipment?.total_gross_weight || 0"
            :precision="2"
            suffix="kg"
          />
        </Card>
      </Col>
      <Col :xs="24" :sm="12" :md="8">
        <Card :bordered="true">
          <Statistic
            title="总件数"
            :value="shipment?.total_packages || 0"
            suffix="箱"
          />
        </Card>
      </Col>
    </Row>
  </div>
</template>

