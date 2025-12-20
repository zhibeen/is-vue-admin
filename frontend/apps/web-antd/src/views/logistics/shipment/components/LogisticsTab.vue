<script setup lang="ts">
/**
 * 发货单详情 - 物流跟踪Tab
 */
import { Card, Descriptions, Row, Col, Timeline, TimelineItem, Input, Select } from 'ant-design-vue';
import { EnvironmentOutlined } from '@ant-design/icons-vue';
import type { Shipment } from '#/api/logistics/shipment';

const DescriptionsItem = Descriptions.Item;

interface Props {
  shipment: Shipment | null;
  isEditing: boolean;
  editForm: any;
}

const props = defineProps<Props>();
</script>

<template>
  <Row :gutter="24">
    <Col :xs="24" :lg="12">
      <Card title="发货信息" size="small" class="mb-4">
        <Descriptions :column="1" bordered size="small">
          <DescriptionsItem label="发货公司">
            {{ shipment?.shipper_company_name || '-' }}
          </DescriptionsItem>
          <DescriptionsItem label="收货人">
            <Input
              v-if="isEditing"
              v-model:value="editForm.consignee_name"
              placeholder="请输入收货人名称"
            />
            <template v-else>
              {{ shipment?.consignee_name || '-' }}
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="收货国家">
            <Input
              v-if="isEditing"
              v-model:value="editForm.consignee_country"
              placeholder="请输入收货国家"
            />
            <template v-else>
              {{ shipment?.consignee_country || '-' }}
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="收货地址">
            <Input.TextArea
              v-if="isEditing"
              v-model:value="editForm.consignee_address"
              placeholder="请输入收货地址"
              :rows="3"
            />
            <template v-else>
              {{ shipment?.consignee_address || '-' }}
            </template>
          </DescriptionsItem>
        </Descriptions>
      </Card>
      
      <Card title="物流详情" size="small">
        <Descriptions :column="1" bordered size="small">
          <DescriptionsItem label="物流商">
            <Input
              v-if="isEditing"
              v-model:value="editForm.logistics_provider"
              placeholder="请输入物流商"
            />
            <template v-else>
              {{ shipment?.logistics_provider || '-' }}
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="服务类型">
            {{ shipment?.logistics_service_type || '-' }}
          </DescriptionsItem>
          <DescriptionsItem label="物流单号">
            <Input
              v-if="isEditing"
              v-model:value="editForm.tracking_no"
              placeholder="请输入物流单号"
            />
            <template v-else>
              {{ shipment?.tracking_no || '-' }}
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="运输方式">
            <Select
              v-if="isEditing"
              v-model:value="editForm.shipping_method"
              placeholder="请选择运输方式"
              style="width: 100%"
            >
              <Select.Option value="海运">海运</Select.Option>
              <Select.Option value="空运">空运</Select.Option>
              <Select.Option value="快递">快递</Select.Option>
              <Select.Option value="陆运">陆运</Select.Option>
            </Select>
            <template v-else>
              {{ shipment?.shipping_method || '-' }}
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="运费条款">
            {{ 
              shipment?.freight_term === 'prepaid' ? '预付' :
              shipment?.freight_term === 'collect' ? '到付' :
              shipment?.freight_term === 'third_party' ? '第三方支付' :
              shipment?.freight_term || '-'
            }}
          </DescriptionsItem>
          <DescriptionsItem label="总件数">
            <Input
              v-if="isEditing"
              v-model:value="editForm.total_packages"
              type="number"
              suffix="箱"
              placeholder="请输入总件数"
            />
            <template v-else>
              {{ shipment?.total_packages || '-' }} 箱
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="总毛重">
            <Input
              v-if="isEditing"
              v-model:value="editForm.total_gross_weight"
              type="number"
              suffix="kg"
              placeholder="请输入总毛重"
            />
            <template v-else>
              {{ shipment?.total_gross_weight || '-' }} kg
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="总净重">
            <Input
              v-if="isEditing"
              v-model:value="editForm.total_net_weight"
              type="number"
              suffix="kg"
              placeholder="请输入总净重"
            />
            <template v-else>
              {{ shipment?.total_net_weight || '-' }} kg
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="总体积">
            <Input
              v-if="isEditing"
              v-model:value="editForm.total_volume"
              type="number"
              suffix="m³"
              placeholder="请输入总体积"
            />
            <template v-else>
              {{ shipment?.total_volume || '-' }} m³
            </template>
          </DescriptionsItem>
          <DescriptionsItem label="包装方式">
            {{ shipment?.packing_method || '-' }}
          </DescriptionsItem>
          <DescriptionsItem label="体积重">
            {{ shipment?.volumetric_weight || '-' }} kg
          </DescriptionsItem>
          <DescriptionsItem label="计费重量">
            <span class="font-semibold">
              {{ shipment?.chargeable_weight || '-' }} kg
            </span>
            <div class="text-xs text-gray-500 mt-1">
              取实重和体积重的较大值
            </div>
          </DescriptionsItem>
        </Descriptions>
      </Card>
    </Col>
    
    <Col :xs="24" :lg="12">
      <Card title="物流时间轴" size="small">
        <Timeline mode="left">
          <!-- 创建发货单 -->
          <TimelineItem color="green">
            <p class="font-semibold text-sm mb-1">📝 创建发货单</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ shipment?.created_at }}</p>
          </TimelineItem>
          
          <!-- 发货单确认 -->
          <TimelineItem 
            v-if="shipment?.status === 'confirmed' || shipment?.status === 'shipped' || shipment?.status === 'completed'"
            color="blue"
          >
            <p class="font-semibold text-sm mb-1">✅ 发货单确认</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              预计发货: {{ shipment?.estimated_ship_date || '-' }}
            </p>
          </TimelineItem>
          
          <!-- 实际发货 -->
          <TimelineItem 
            v-if="shipment?.actual_ship_date"
            color="cyan"
          >
            <p class="font-semibold text-sm mb-1">🚚 实际发货</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ shipment?.actual_ship_date }}
            </p>
            <p class="text-xs text-gray-400 mt-1">
              预计到达: {{ shipment?.estimated_arrival_date || '-' }}
            </p>
          </TimelineItem>
          <TimelineItem v-else-if="shipment?.status === 'confirmed'" color="gray">
            <p class="font-semibold text-sm text-gray-400">⏳ 待发货...</p>
          </TimelineItem>
          
          <!-- 实际到达 -->
          <TimelineItem 
            v-if="shipment?.actual_arrival_date"
            color="orange"
          >
            <p class="font-semibold text-sm mb-1">📍 货物到达</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ shipment?.actual_arrival_date }}
            </p>
          </TimelineItem>
          <TimelineItem v-else-if="shipment?.status === 'shipped'" color="gray">
            <p class="font-semibold text-sm text-gray-400">🚢 运输中...</p>
            <p class="text-xs text-gray-400 mt-1">
              预计: {{ shipment?.estimated_arrival_date || '-' }}
            </p>
          </TimelineItem>
          
          <!-- 仓库签收 -->
          <TimelineItem 
            v-if="shipment?.warehouse_received_date"
            color="purple"
          >
            <p class="font-semibold text-sm mb-1">📦 仓库签收</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ shipment?.warehouse_received_date }}
            </p>
          </TimelineItem>
          
          <!-- 完成 -->
          <TimelineItem 
            v-if="shipment?.completed_date"
            color="green"
          >
            <p class="font-semibold text-sm mb-1">✔️ 完成</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ shipment?.completed_date }}
            </p>
          </TimelineItem>
        </Timeline>
      </Card>
    </Col>
  </Row>
</template>

