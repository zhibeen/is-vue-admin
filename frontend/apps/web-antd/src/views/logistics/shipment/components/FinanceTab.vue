<script setup lang="ts">
/**
 * 发货单详情 - 物流成本Tab
 * 仅记录物流相关成本，不涉及完整财务核算
 */
import { Card, Descriptions, Row, Col, Statistic, Alert, Empty } from 'ant-design-vue';
import { DollarOutlined } from '@ant-design/icons-vue';
import type { Shipment } from '#/api/logistics/shipment';

const DescriptionsItem = Descriptions.Item;

interface Props {
  shipment: Shipment | null;
}

const props = defineProps<Props>();

// 格式化金额
const formatAmount = (amount: number | undefined | null) => {
  if (amount === undefined || amount === null) return '-';
  return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

// 检查是否有物流成本数据
const hasLogisticsCost = () => {
  return props.shipment?.freight_cost || 
         props.shipment?.insurance_cost || 
         props.shipment?.handling_fee || 
         props.shipment?.other_costs;
};
</script>

<template>
  <div>
    <!-- 说明提示 -->
    <Alert 
      type="info" 
      show-icon 
      class="mb-4"
    >
      <template #message>
        <span class="font-semibold">关于物流成本</span>
      </template>
      <template #description>
        <p class="text-sm">
          此处仅记录与本次发货直接相关的物流成本，包括运费、保险费、操作费等。
          完整的财务核算（采购成本、利润分析等）请在财务系统中查看。
        </p>
      </template>
    </Alert>
    
    <!-- 物流成本概览 -->
    <div v-if="hasLogisticsCost()">
      <Row :gutter="16" class="mb-4">
        <Col :xs="24" :sm="12" :md="8">
          <Card :bordered="true" size="small">
            <Statistic
              title="物流总成本"
              :value="shipment?.total_logistics_cost || 0"
              :precision="2"
              prefix="¥"
              :value-style="{ color: '#cf1322', fontSize: '24px' }"
            />
          </Card>
        </Col>
        <Col :xs="24" :sm="12" :md="8">
          <Card :bordered="true" size="small">
            <Statistic
              title="运费"
              :value="shipment?.freight_cost || 0"
              :precision="2"
              prefix="¥"
            />
          </Card>
        </Col>
        <Col :xs="24" :sm="12" :md="8">
          <Card :bordered="true" size="small">
            <Statistic
              title="保险费"
              :value="shipment?.insurance_cost || 0"
              :precision="2"
              prefix="¥"
            />
          </Card>
        </Col>
      </Row>
      
      <!-- 成本明细 -->
      <Card title="物流成本明细" size="small" class="mb-4">
        <Descriptions :column="2" bordered size="small">
          <DescriptionsItem label="币种">
            {{ shipment?.currency || 'CNY' }}
          </DescriptionsItem>
          <DescriptionsItem label="运费条款">
            <span v-if="shipment?.freight_term">
              {{ 
                shipment.freight_term === 'prepaid' ? '预付（Prepaid）' :
                shipment.freight_term === 'collect' ? '到付（Collect）' :
                shipment.freight_term === 'third_party' ? '第三方支付（Third Party）' :
                shipment.freight_term
              }}
            </span>
            <span v-else>-</span>
          </DescriptionsItem>
          <DescriptionsItem label="运费">
            <span class="text-base">{{ formatAmount(shipment?.freight_cost) }}</span>
            <div class="text-xs text-gray-500 mt-1">
              基于 {{ shipment?.chargeable_weight || '-' }} kg 计费重量
            </div>
          </DescriptionsItem>
          <DescriptionsItem label="保险费">
            {{ formatAmount(shipment?.insurance_cost) }}
          </DescriptionsItem>
          <DescriptionsItem label="操作费">
            {{ formatAmount(shipment?.handling_fee) }}
          </DescriptionsItem>
          <DescriptionsItem label="其他费用">
            {{ formatAmount(shipment?.other_costs) }}
          </DescriptionsItem>
          <DescriptionsItem label="物流总成本" :span="2">
            <span class="text-lg font-semibold text-red-600">
              {{ formatAmount(shipment?.total_logistics_cost) }}
            </span>
          </DescriptionsItem>
        </Descriptions>
      </Card>
      
      <!-- 成本说明 -->
      <Alert 
        type="warning" 
        show-icon 
        class="mt-4"
      >
        <template #message>
          <span class="font-semibold">成本说明</span>
        </template>
        <template #description>
          <ul class="list-disc list-inside space-y-1 text-sm">
            <li>运费根据实际重量和体积重的较大值（计费重量）计算</li>
            <li>保险费通常为货值的0.3%-0.5%</li>
            <li>操作费包括装卸、打托、贴标等人工成本</li>
            <li>运费条款决定了费用由谁承担：预付（发货方）、到付（收货方）或第三方</li>
            <li>
              <span class="text-orange-600 font-medium">
                注意：此处仅为物流成本记录，不包括采购成本、关税等其他费用
              </span>
            </li>
          </ul>
        </template>
      </Alert>
    </div>
    
    <!-- 无成本数据时 -->
    <div v-else>
      <Empty 
        description="暂无物流成本数据"
        class="my-8"
      >
        <template #image>
          <DollarOutlined style="font-size: 48px; color: #d9d9d9;" />
        </template>
        <p class="text-sm text-gray-500 mt-4">
          物流成本将在确认运输方式和物流商后录入
        </p>
      </Empty>
    </div>
    
    <!-- 底部提示 -->
    <div class="mt-6 p-4 bg-blue-50 dark:bg-gray-800 rounded border border-blue-200 dark:border-gray-700">
      <p class="text-sm text-gray-700 dark:text-gray-300">
        <span class="font-semibold">💡 关于完整财务核算：</span>
        如需查看完整的财务信息（采购成本、销售收入、利润分析等），请前往
        <a href="#" class="text-blue-600 hover:text-blue-800 underline">财务管理系统</a>。
        发货单仅负责记录物流环节的直接成本。
      </p>
    </div>
  </div>
</template>
