<script setup lang="ts">
/**
 * 发货单详情 - 概览Tab
 */
import { Card, Descriptions, Tag, Button, Space, Table, Row, Col } from 'ant-design-vue';
import { InfoCircleOutlined } from '@ant-design/icons-vue';
import { useRouter } from 'vue-router';
import type { Shipment } from '#/api/logistics/shipment';
import { Input } from 'ant-design-vue';

const DescriptionsItem = Descriptions.Item;

interface Props {
  shipment: Shipment | null;
  isEditing: boolean;
  editForm: any;
}

interface Emits {
  (e: 'switchTab', tabKey: string): void;
  (e: 'confirm'): void;
  (e: 'generateContracts'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();
const router = useRouter();

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

// 概览Tab显示的商品列（更简洁）
const overviewColumns = [
  {
    title: 'SKU',
    dataIndex: 'sku',
    key: 'sku',
    width: 120,
  },
  {
    title: '品名',
    dataIndex: 'product_name',
    key: 'product_name',
    width: 180,
  },
  {
    title: 'HS CODE',
    dataIndex: 'hs_code',
    key: 'hs_code',
    width: 110,
  },
  {
    title: '数量',
    dataIndex: 'quantity',
    key: 'quantity',
    width: 80,
    align: 'right' as const,
  },
  {
    title: '申报单位',
    dataIndex: 'customs_unit',
    key: 'customs_unit',
    width: 90,
  },
];
</script>

<template>
  <Row :gutter="24">
    <!-- 左侧：核心信息 -->
    <Col :xs="24" :lg="16">
      <!-- 基本信息 -->
      <Card title="基本信息" size="small" class="mb-4">
        <Descriptions :column="2" bordered size="small">
          <DescriptionsItem label="发货单号">
            {{ shipment?.shipment_no }}
          </DescriptionsItem>
          <DescriptionsItem label="状态">
            <Tag :color="statusColorMap[shipment?.status || '']">
              {{ statusTextMap[shipment?.status || ''] }}
            </Tag>
          </DescriptionsItem>
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
        </Descriptions>
      </Card>
      
      <!-- 商品明细（前5条） -->
      <Card title="商品明细" size="small">
        <Table
          :columns="overviewColumns"
          :data-source="shipment?.items?.slice(0, 5) || []"
          :pagination="false"
          row-key="id"
          size="small"
          bordered
        />
        <div v-if="shipment?.items && shipment.items.length > 5" class="mt-3 text-center">
          <Button type="link" @click="emit('switchTab', 'goods')">
            查看全部 {{ shipment.items.length }} 条商品 →
          </Button>
        </div>
      </Card>
    </Col>
    
    <!-- 右侧：快捷操作 -->
    <Col :xs="24" :lg="8">
      <Card title="快捷操作" size="small" class="mb-4">
        <Space direction="vertical" style="width: 100%" size="middle">
          <Button 
            v-if="shipment?.status === 'draft'" 
            type="primary" 
            block 
            @click="emit('confirm')"
          >
            确认发货单
          </Button>
          <Button 
            v-if="shipment?.status === 'confirmed' && !shipment.is_contracted"
            type="primary" 
            block 
            @click="emit('generateContracts')"
          >
            生成交付合同
          </Button>
          <Button block>
            下载PDF
          </Button>
          <Button block>
            打印发货单
          </Button>
        </Space>
      </Card>
      
      <Card title="关联单据" size="small">
        <Space direction="vertical" style="width: 100%" size="small">
          <div class="flex items-center justify-between">
            <span>报关单：</span>
            <Space>
              <Tag :color="shipment?.is_declared ? 'success' : 'default'">
                {{ shipment?.is_declared ? '已生成' : '未生成' }}
              </Tag>
              <Button 
                v-if="shipment?.customs_declaration_id"
                type="link" 
                size="small"
                @click="router.push(`/customs/declaration/${shipment.customs_declaration_id}`)"
              >
                查看
              </Button>
            </Space>
          </div>
          <div class="flex items-center justify-between">
            <span>交付合同：</span>
            <Tag :color="shipment?.is_contracted ? 'success' : 'default'">
              {{ shipment?.is_contracted ? '已生成' : '未生成' }}
            </Tag>
          </div>
        </Space>
      </Card>
    </Col>
  </Row>
</template>

