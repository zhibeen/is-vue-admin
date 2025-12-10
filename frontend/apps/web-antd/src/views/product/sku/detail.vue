<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { Card, Descriptions, Tag, Button, Tabs, Space, message } from 'ant-design-vue';
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons-vue';
import { getSkuDetailApi } from '#/api/core/product';
import type { SkuDetail } from '#/api/core/product';

const route = useRoute();
const router = useRouter();
const sku = ref<string>(route.params.sku as string);
const loading = ref(false);
const skuDetail = ref<SkuDetail | null>(null);

// 使用模拟数据
const mockSkuDetail = {
  sku: '101120501DWD',
  feature_code: 'HL-CHE-SIL-07-13-D-WB',
  product_id: 1,
  product_name: '雪佛兰Silverado前大灯',
  spu_code: 'HL-CHE-SIL-07-13',
  category_id: 1,
  category_name: '前大灯',
  brand: '雪佛兰',
  model: 'Silverado',
  attributes: {
    position: '左侧',
    color: '黑色',
    material: 'ABS塑料',
    voltage: '12V',
  },
  attributes_display: '左侧,黑色,ABS塑料,12V',
  compliance_info: {
    hs_code: '85122090',
    declared_name: '汽车前大灯总成',
    declared_unit: '个',
    net_weight: 2.5,
    gross_weight: 3.2,
    package_dimensions: '40×30×25cm',
  },
  coding_rules: {
    category_code: '101',
    vehicle_code: '1205',
    brand_code: '12',
    model_code: '05',
    serial: '01',
    suffix: 'DWD',
    category_abbreviation: 'HL',
    category_code_db: '101',
  },
  reference_codes: [
    { code: '12345678', code_type: 'OE', brand: 'GM' },
    { code: 'HL-1234', code_type: 'OEM', brand: 'TYC' },
  ],
  fitments: [
    { make: '雪佛兰', model: 'Silverado', sub_model: '1500', year_start: 2007, year_end: 2013, position: '前左侧' },
    { make: '雪佛兰', model: 'Silverado', sub_model: '2500', year_start: 2007, year_end: 2013, position: '前左侧' },
  ],
  stock_quantity: 150,
  safety_stock: 50,
  in_transit: 30,
  warning_status: 'normal',
  quality_type: 'Aftermarket',
  is_active: true,
  created_at: '2024-01-15T10:30:00',
  updated_at: '2024-01-20T14:15:00',
};

// 标签页配置
const tabItems = [
  {
    key: 'attributes',
    label: '属性详情',
  },
  {
    key: 'compliance',
    label: '合规信息',
  },
  {
    key: 'inventory',
    label: '库存记录',
  },
  {
    key: 'history',
    label: '操作历史',
  },
];

// 计算属性
const basicInfo = computed(() => {
  if (!skuDetail.value) return null;
  return {
    product_name: skuDetail.value.product_name,
    category_name: skuDetail.value.category_name,
    brand_model: `${skuDetail.value.brand || '-'}/${skuDetail.value.model || '-'}`,
    attributes_display: skuDetail.value.attributes_display,
    quality_type: skuDetail.value.quality_type || 'Aftermarket',
    is_active: skuDetail.value.is_active,
  };
});

const codeInfo = computed(() => {
  if (!skuDetail.value) return null;
  return {
    sku: skuDetail.value.sku,
    feature_code: skuDetail.value.feature_code,
    spu_code: skuDetail.value.spu_code,
    coding_rules: skuDetail.value.coding_rules,
  };
});

const inventoryInfo = computed(() => {
  if (!skuDetail.value) return null;
  return {
    stock_quantity: skuDetail.value.stock_quantity || 0,
    safety_stock: skuDetail.value.safety_stock || 0,
    in_transit: skuDetail.value.in_transit || 0,
    warning_status: skuDetail.value.warning_status || 'normal',
  };
});

// 方法
async function loadSkuDetail() {
  try {
    loading.value = true;
    // 使用模拟数据
    skuDetail.value = mockSkuDetail;
    
    // 如果是真实API调用，取消注释以下代码
    // const res = await getSkuDetailApi(sku.value);
    // skuDetail.value = (res as any).data || res;
    
  } catch (error) {
    console.error('Failed to load SKU detail:', error);
    message.error('加载SKU详情失败，使用模拟数据');
    // 使用模拟数据作为fallback
    skuDetail.value = mockSkuDetail;
  } finally {
    loading.value = false;
  }
}

function handleBack() {
  router.push('/product/sku');
}

function handleEdit() {
  router.push(`/product/spu/edit/${skuDetail.value?.product_id}?variant=${sku.value}`);
}

function handleToggleStatus() {
  // TODO: Implement toggle status
  message.info('状态切换功能待实现');
}

onMounted(() => {
  loadSkuDetail();
});
</script>

<template>
  <Page auto-content-height :title="`SKU详情 - ${sku}`" :loading="loading">
    <!-- 头部操作栏 -->
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Button @click="handleBack">
          <ArrowLeftOutlined /> 返回列表
        </Button>
        <span class="text-lg font-semibold">SKU: {{ sku }}</span>
      </div>
      <Space>
        <Button @click="handleToggleStatus">
          {{ skuDetail?.is_active ? '停用' : '启用' }}
        </Button>
        <Button type="primary" @click="handleEdit">
          <EditOutlined /> 编辑
        </Button>
      </Space>
    </div>

    <!-- 三栏布局 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
      <!-- 基本信息 -->
      <Card title="基本信息" size="small">
        <Descriptions v-if="basicInfo" :column="1" size="small">
          <Descriptions.Item label="产品名称">
            {{ basicInfo.product_name }}
          </Descriptions.Item>
          <Descriptions.Item label="所属分类">
            {{ basicInfo.category_name }}
          </Descriptions.Item>
          <Descriptions.Item label="品牌/车型">
            {{ basicInfo.brand_model }}
          </Descriptions.Item>
          <Descriptions.Item label="属性组合">
            <span class="text-gray-600">{{ basicInfo.attributes_display }}</span>
          </Descriptions.Item>
          <Descriptions.Item label="质量类型">
            <Tag>{{ basicInfo.quality_type }}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag :color="basicInfo.is_active ? 'success' : 'error'">
              {{ basicInfo.is_active ? '启用' : '停用' }}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <!-- 编码信息 -->
      <Card title="编码信息" size="small">
        <Descriptions v-if="codeInfo" :column="1" size="small">
          <Descriptions.Item label="SKU编码">
            <span class="font-mono font-bold">{{ codeInfo.sku }}</span>
          </Descriptions.Item>
          <Descriptions.Item label="特征码">
            <span class="font-mono">{{ codeInfo.feature_code }}</span>
          </Descriptions.Item>
          <Descriptions.Item label="SPU编码">
            <span class="font-mono text-primary cursor-pointer hover:underline" 
                  @click="router.push(`/product/spu/detail/${skuDetail?.product_id}`)">
              {{ codeInfo.spu_code }}
            </span>
          </Descriptions.Item>
          <Descriptions.Item label="编码规则">
            <div class="text-xs text-gray-500 mt-1">
              <div>• 类目码(3位): {{ codeInfo.coding_rules?.category_code || 'N/A' }}</div>
              <div>• 车型码(4位): {{ codeInfo.coding_rules?.vehicle_code || 'N/A' }}</div>
              <div>• 流水号(2位): {{ codeInfo.coding_rules?.serial || 'N/A' }}</div>
              <div>• 属性后缀: {{ codeInfo.coding_rules?.suffix || '无' }}</div>
            </div>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <!-- 库存信息 -->
      <Card title="库存信息" size="small">
        <Descriptions v-if="inventoryInfo" :column="1" size="small">
          <Descriptions.Item label="当前库存">
            <Tag :color="inventoryInfo.stock_quantity > 0 ? 'success' : 'error'">
              {{ inventoryInfo.stock_quantity }}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="安全库存">
            {{ inventoryInfo.safety_stock }}
          </Descriptions.Item>
          <Descriptions.Item label="在途数量">
            {{ inventoryInfo.in_transit }}
          </Descriptions.Item>
          <Descriptions.Item label="预警状态">
            <Tag :color="inventoryInfo.warning_status === 'warning' ? 'warning' : 
                         inventoryInfo.warning_status === 'danger' ? 'danger' : 'success'">
              {{ inventoryInfo.warning_status === 'warning' ? '预警' : 
                 inventoryInfo.warning_status === 'danger' ? '缺货' : '正常' }}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>

    <!-- 标签页内容 -->
    <Card>
      <Tabs :items="tabItems">
        <template #attributes>
          <div v-if="skuDetail?.attributes" class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-for="(value, key) in skuDetail.attributes" :key="key" class="border rounded p-3">
                <div class="font-medium text-gray-700">{{ key }}</div>
                <div class="mt-1 text-gray-900">{{ value }}</div>
              </div>
            </div>
          </div>
          <div v-else class="p-8 text-center text-gray-400">
            暂无属性信息
          </div>
        </template>

        <template #compliance>
          <div v-if="skuDetail?.compliance_info" class="p-4">
            <Descriptions :column="2" size="small">
              <Descriptions.Item label="HS编码">
                {{ skuDetail.compliance_info.hs_code || '-' }}
              </Descriptions.Item>
              <Descriptions.Item label="申报品名">
                {{ skuDetail.compliance_info.declared_name || '-' }}
              </Descriptions.Item>
              <Descriptions.Item label="申报单位">
                {{ skuDetail.compliance_info.declared_unit || '-' }}
              </Descriptions.Item>
              <Descriptions.Item label="净重(KG)">
                {{ skuDetail.compliance_info.net_weight || '-' }}
              </Descriptions.Item>
              <Descriptions.Item label="毛重(KG)">
                {{ skuDetail.compliance_info.gross_weight || '-' }}
              </Descriptions.Item>
              <Descriptions.Item label="包装尺寸">
                {{ skuDetail.compliance_info.package_dimensions || '-' }}
              </Descriptions.Item>
            </Descriptions>
          </div>
          <div v-else class="p-8 text-center text-gray-400">
            暂无合规信息
          </div>
        </template>

        <template #inventory>
          <div class="p-8 text-center text-gray-400">
            库存记录功能待实现
          </div>
        </template>

        <template #history>
          <div class="p-8 text-center text-gray-400">
            操作历史功能待实现
          </div>
        </template>
      </Tabs>
    </Card>
  </Page>
</template>
