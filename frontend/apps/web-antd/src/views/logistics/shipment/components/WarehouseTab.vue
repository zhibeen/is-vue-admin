<script setup lang="ts">
/**
 * 发货单详情 - 仓库信息Tab
 */
import { Card, Descriptions, Row, Col, Tag, Alert } from 'ant-design-vue';
import { HomeOutlined } from '@ant-design/icons-vue';
import type { Shipment } from '#/api/logistics/shipment';

const DescriptionsItem = Descriptions.Item;

interface Props {
  shipment: Shipment | null;
}

const props = defineProps<Props>();

// 仓库类型标签
const warehouseTypeMap: Record<string, { text: string; color: string }> = {
  fba: { text: 'FBA仓库', color: 'blue' },
  third_party: { text: '第三方仓', color: 'green' },
  self: { text: '自营仓', color: 'orange' },
};

const originTypeMap: Record<string, string> = {
  self: '自营仓',
  factory: '工厂仓',
  supplier: '供应商仓',
};
</script>

<template>
  <div>
    <!-- 业务场景提示 -->
    <Alert 
      v-if="shipment?.destination_warehouse_type"
      :type="shipment.destination_warehouse_type === 'fba' ? 'info' : 'success'"
      show-icon 
      class="mb-4"
    >
      <template #message>
        <span class="font-semibold">
          当前业务场景: 
          <Tag :color="warehouseTypeMap[shipment.destination_warehouse_type]?.color || 'default'">
            {{ warehouseTypeMap[shipment.destination_warehouse_type]?.text || shipment.destination_warehouse_type }}
          </Tag>
        </span>
      </template>
    </Alert>
    
    <Row :gutter="24">
      <!-- 发货仓库 -->
      <Col :xs="24" :lg="12">
        <Card title="发货仓库" size="small" class="mb-4">
          <Descriptions :column="1" bordered size="small">
            <DescriptionsItem label="仓库名称">
              {{ shipment?.origin_warehouse_name || '-' }}
            </DescriptionsItem>
            <DescriptionsItem label="仓库类型">
              <Tag>{{ originTypeMap[shipment?.origin_warehouse_type || ''] || shipment?.origin_warehouse_type || '-' }}</Tag>
            </DescriptionsItem>
            <DescriptionsItem label="仓库地址">
              {{ shipment?.origin_warehouse_address || '-' }}
            </DescriptionsItem>
            <DescriptionsItem label="工厂直发">
              <Tag :color="shipment?.is_factory_direct ? 'green' : 'default'">
                {{ shipment?.is_factory_direct ? '是' : '否' }}
              </Tag>
            </DescriptionsItem>
          </Descriptions>
        </Card>
      </Col>
      
      <!-- 收货仓库 -->
      <Col :xs="24" :lg="12">
        <Card title="收货仓库" size="small" class="mb-4">
          <Descriptions :column="1" bordered size="small">
            <DescriptionsItem label="仓库名称">
              {{ shipment?.destination_warehouse_name || '-' }}
            </DescriptionsItem>
            <DescriptionsItem label="仓库编码">
              <Tag color="blue">{{ shipment?.destination_warehouse_code || '-' }}</Tag>
            </DescriptionsItem>
            <DescriptionsItem label="仓库类型">
              <Tag :color="warehouseTypeMap[shipment?.destination_warehouse_type || '']?.color || 'default'">
                {{ warehouseTypeMap[shipment?.destination_warehouse_type || '']?.text || shipment?.destination_warehouse_type || '-' }}
              </Tag>
            </DescriptionsItem>
            <DescriptionsItem label="仓库地址">
              {{ shipment?.destination_warehouse_address || '-' }}
            </DescriptionsItem>
          </Descriptions>
        </Card>
      </Col>
    </Row>
    
    <!-- FBA特定信息 -->
    <Card 
      v-if="shipment?.destination_warehouse_type === 'fba'" 
      title="FBA信息" 
      size="small"
      class="mb-4"
    >
      <Descriptions :column="2" bordered size="small">
        <DescriptionsItem label="FBA发货计划ID">
          <Tag color="blue">{{ shipment?.fba_shipment_id || '-' }}</Tag>
        </DescriptionsItem>
        <DescriptionsItem label="市场站点">
          <Tag color="orange">{{ shipment?.marketplace || '-' }}</Tag>
        </DescriptionsItem>
        <DescriptionsItem label="FBA配送中心" :span="2">
          <div v-if="shipment?.fba_center_codes && shipment.fba_center_codes.length > 0" class="flex gap-2">
            <Tag v-for="center in shipment.fba_center_codes" :key="center" color="purple">
              {{ center }}
            </Tag>
          </div>
          <span v-else>-</span>
        </DescriptionsItem>
      </Descriptions>
      
      <Alert 
        type="info" 
        show-icon 
        class="mt-4"
        message="FBA发货注意事项"
      >
        <template #description>
          <ul class="list-disc list-inside space-y-1 text-sm">
            <li>请确保每个SKU都有对应的FNSKU标签</li>
            <li>商品需要按照FBA包装要求进行包装</li>
            <li>发货前请在Seller Central创建发货计划</li>
            <li>使用FBA专用运输标签</li>
          </ul>
        </template>
      </Alert>
    </Card>
    
    <!-- 第三方仓特定信息 -->
    <Card 
      v-if="shipment?.destination_warehouse_type === 'third_party'" 
      title="第三方仓储信息" 
      size="small"
      class="mb-4"
    >
      <Descriptions :column="2" bordered size="small">
        <DescriptionsItem label="服务商">
          {{ shipment?.warehouse_service_provider || '-' }}
        </DescriptionsItem>
        <DescriptionsItem label="联系人">
          {{ shipment?.warehouse_contact || '-' }}
        </DescriptionsItem>
        <DescriptionsItem label="联系电话" :span="2">
          {{ shipment?.warehouse_contact_phone || '-' }}
        </DescriptionsItem>
      </Descriptions>
      
      <Alert 
        type="success" 
        show-icon 
        class="mt-4"
        message="第三方仓发货注意事项"
      >
        <template #description>
          <ul class="list-disc list-inside space-y-1 text-sm">
            <li>发货前请与仓储服务商确认收货时间</li>
            <li>提供准确的SKU清单和数量</li>
            <li>商品需要按照服务商要求进行标识</li>
            <li>保持与仓储服务商的沟通</li>
          </ul>
        </template>
      </Alert>
    </Card>
  </div>
</template>

