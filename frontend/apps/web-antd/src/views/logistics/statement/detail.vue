<template>
  <div class="p-4">
    <Card class="mb-4">
      <template #title>
        <div class="flex items-center justify-between">
          <Space>
            <Button @click="handleBack">
              <template #icon>
                <ArrowLeftOutlined />
              </template>
              返回
            </Button>
            <span class="text-lg font-semibold">对账单详情</span>
          </Space>
          <Space>
            <Button
              v-if="statement?.status === 'draft'"
              type="primary"
              @click="handleConfirm"
            >
              确认对账单
            </Button>
            <Button
              v-if="statement?.status === 'confirmed'"
              type="primary"
              @click="handleSubmit"
            >
              提交财务
            </Button>
          </Space>
        </div>
      </template>

      <Spin :spinning="loading">
        <Descriptions
          v-if="statement"
          bordered
          :column="2"
        >
          <DescriptionsItem label="对账单号">
            {{ statement.statement_no }}
          </DescriptionsItem>
          <DescriptionsItem label="状态">
            <Tag :color="statusConfig[statement.status]?.color">
              {{ statusConfig[statement.status]?.text || statement.status }}
            </Tag>
          </DescriptionsItem>
          <DescriptionsItem label="物流服务商">
            {{ statement.logistics_provider?.provider_name || '-' }}
          </DescriptionsItem>
          <DescriptionsItem label="对账周期">
            {{ statement.statement_period_start }} ~ {{ statement.statement_period_end }}
          </DescriptionsItem>
          <DescriptionsItem label="总金额">
            <span class="text-red-600 text-lg font-semibold">
              ¥{{ Number(statement.total_amount).toFixed(2) }}
            </span>
          </DescriptionsItem>
          <DescriptionsItem label="币种">
            {{ statement.currency }}
          </DescriptionsItem>
          <DescriptionsItem label="确认人">
            {{ statement.confirmed_by?.nickname || '-' }}
          </DescriptionsItem>
          <DescriptionsItem label="确认时间">
            {{ statement.confirmed_at || '-' }}
          </DescriptionsItem>
          <DescriptionsItem label="创建时间">
            {{ statement.created_at }}
          </DescriptionsItem>
          <DescriptionsItem label="财务应付单ID">
            {{ statement.finance_payable_id || '-' }}
          </DescriptionsItem>
          <DescriptionsItem label="备注" :span="2">
            {{ statement.notes || '-' }}
          </DescriptionsItem>
        </Descriptions>
      </Spin>
    </Card>

    <!-- 关联的物流服务明细 -->
    <Card title="关联物流服务明细">
      <div class="text-gray-500">功能开发中，将展示关联的物流服务列表</div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import {
  Card,
  Button,
  Space,
  Descriptions,
  DescriptionsItem,
  Tag,
  Spin,
  Modal,
  message,
} from 'ant-design-vue';
import { ArrowLeftOutlined } from '@ant-design/icons-vue';
import {
  getStatementDetailApi,
  confirmStatementApi,
  submitStatementToFinanceApi,
  type LogisticsStatement,
} from '#/api/logistics/statement';

const router = useRouter();
const route = useRoute();

const statement = ref<LogisticsStatement | null>(null);
const loading = ref(false);

const statusConfig: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  confirmed: { color: 'processing', text: '已确认' },
  submitted: { color: 'warning', text: '已提交' },
  approved: { color: 'success', text: '已批准' },
  paid: { color: 'success', text: '已付款' },
};

// 加载详情
async function loadDetail() {
  const id = Number(route.params.id);
  if (!id) return;

  try {
    loading.value = true;
    statement.value = await getStatementDetailApi(id);
  } catch (error: any) {
    message.error(error.message || '加载失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 返回列表
function handleBack() {
  router.push('/logistics/statement');
}

// 确认对账单
function handleConfirm() {
  if (!statement.value) return;

  Modal.confirm({
    title: '确认对账单',
    content: '确认后对账单将锁定，无法再修改。是否继续？',
    async onOk() {
      try {
        await confirmStatementApi(statement.value!.id);
        message.success('确认成功');
        loadDetail();
      } catch (error: any) {
        message.error(error.message || '确认失败');
        console.error(error);
      }
    },
  });
}

// 提交财务
function handleSubmit() {
  if (!statement.value) return;

  Modal.confirm({
    title: '提交财务',
    content: '提交后将生成财务应付单，是否继续？',
    async onOk() {
      try {
        await submitStatementToFinanceApi(statement.value!.id);
        message.success('提交成功');
        loadDetail();
      } catch (error: any) {
        message.error(error.message || '提交失败');
        console.error(error);
      }
    },
  });
}

onMounted(() => {
  loadDetail();
});
</script>

