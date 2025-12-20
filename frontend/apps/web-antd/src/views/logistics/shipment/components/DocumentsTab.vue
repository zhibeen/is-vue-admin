<script setup lang="ts">
/**
 * 发货单详情 - 关联单据Tab
 */
import { Card, Tag, Button, Space, Row, Col } from 'ant-design-vue';
import { FileTextOutlined } from '@ant-design/icons-vue';
import { useRouter } from 'vue-router';
import type { Shipment } from '#/api/logistics/shipment';

interface Props {
  shipment: Shipment | null;
}

interface Emits {
  (e: 'generateContracts'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();
const router = useRouter();
</script>

<template>
  <Row :gutter="16">
    <Col :xs="24" :sm="12" :lg="8">
      <Card :bordered="true" size="small">
        <template #title>
          <span class="flex items-center gap-2">
            <FileTextOutlined />
            报关单
          </span>
        </template>
        <div class="min-h-[120px]">
          <Tag :color="shipment?.is_declared ? 'success' : 'default'" class="mb-2">
            {{ shipment?.is_declared ? '已生成' : '未生成' }}
          </Tag>
          <div v-if="shipment?.customs_declaration_id" class="mt-3">
            <p class="text-sm text-gray-500">单据编号: {{ shipment.customs_declaration_id }}</p>
            <Space class="mt-2">
              <Button 
                type="primary" 
                size="small"
                @click="router.push(`/customs/declaration/${shipment.customs_declaration_id}`)"
              >
                查看详情
              </Button>
              <Button size="small">下载</Button>
            </Space>
          </div>
          <div v-else class="text-gray-400">
            暂无报关单
          </div>
        </div>
      </Card>
    </Col>
    
    <Col :xs="24" :sm="12" :lg="8">
      <Card :bordered="true" size="small">
        <template #title>
          <span class="flex items-center gap-2">
            <FileTextOutlined />
            交付合同
          </span>
        </template>
        <div class="min-h-[120px]">
          <Tag :color="shipment?.is_contracted ? 'success' : 'default'" class="mb-2">
            {{ shipment?.is_contracted ? '已生成' : '未生成' }}
          </Tag>
          <div v-if="shipment?.is_contracted" class="document-info">
            <Space class="mt-2">
              <Button type="primary" size="small">查看详情</Button>
              <Button size="small">下载</Button>
            </Space>
          </div>
          <div v-else class="text-gray-400">
            <Button 
              v-if="shipment?.status === 'confirmed'"
              type="dashed" 
              size="small"
              @click="emit('generateContracts')"
            >
              立即生成
            </Button>
            <span v-else>暂无合同</span>
          </div>
        </div>
      </Card>
    </Col>
    
    <Col :xs="24" :sm="12" :lg="8">
      <Card :bordered="true" size="small">
        <template #title>
          <span class="flex items-center gap-2">
            <FileTextOutlined />
            外部单据
          </span>
        </template>
        <div class="min-h-[120px]">
          <div class="text-sm mb-2">
            <p><span class="text-gray-500">外部订单号：</span>{{ shipment?.external_order_no || '-' }}</p>
            <p><span class="text-gray-500">外部跟踪号：</span>{{ shipment?.external_tracking_no || '-' }}</p>
          </div>
        </div>
      </Card>
    </Col>
  </Row>
</template>

