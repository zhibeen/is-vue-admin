<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { onMounted, reactive, ref } from 'vue';
import { Button as AButton, Space, Tag, Input, Modal, Radio, message, Form } from 'ant-design-vue';
import { ReloadOutlined, SyncOutlined } from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import { getStockDiscrepancies, resolveStockDiscrepancy, syncAllStock } from '#/api/warehouse/sync';
import type { StockDiscrepancy } from '#/api/warehouse/model';

// --- State ---
const syncLoading = ref(false);
const resolveModal = reactive({
  visible: false,
  loading: false,
  id: 0,
  sku: '',
  form: {
    action: 'sync_to_system' as 'sync_to_system' | 'sync_to_platform' | 'ignore',
    note: '',
  }
});

// --- Grid Config ---
const gridOptions: VxeGridProps = {
  keepSource: true,
  height: 'auto',
  autoResize: true,
  pagerConfig: {
    enabled: true,
    pageSize: 20,
    pageSizes: [10, 20, 50, 100],
  },
  columns: [
    { type: 'seq', width: 50, fixed: 'left' },
    { field: 'sku', title: 'SKU', width: 180, fixed: 'left', sortable: true },
    { field: 'warehouse_name', title: '仓库', width: 150 },
    { 
      field: 'system_qty', 
      title: '系统库存', 
      width: 100, 
      align: 'center' 
    },
    { 
      field: 'actual_qty', 
      title: '平台库存', 
      width: 100, 
      align: 'center' 
    },
    { 
      field: 'diff_qty', 
      title: '差异数量', 
      width: 100, 
      align: 'center',
      slots: { default: 'diff_slot' }
    },
    { 
      field: 'status', 
      title: '状态', 
      width: 100, 
      align: 'center',
      slots: { default: 'status_slot' }
    },
    { field: 'created_at', title: '发现时间', width: 160, sortable: true },
    {
      title: '操作',
      width: 120,
      fixed: 'right',
      slots: { default: 'action_slot' }
    }
  ],
  toolbarConfig: {
    refresh: true,
    custom: true,
    slots: { buttons: 'toolbar_buttons' }
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const res = await getStockDiscrepancies({
            page: page.currentPage,
            per_page: page.pageSize,
            // default showing pending? or all? Let's show all for now.
          });
          return res;
        } catch (error) {
          console.error(error);
          return { items: [], total: 0 };
        }
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

// --- Handlers ---

async function handleSyncAll() {
  try {
    syncLoading.value = true;
    await syncAllStock();
    message.success('全量同步任务已提交，请稍后刷新查看结果');
    gridApi.reload();
  } catch (error) {
    console.error(error);
  } finally {
    syncLoading.value = false;
  }
}

function handleResolve(row: StockDiscrepancy) {
  resolveModal.id = row.id;
  resolveModal.sku = row.sku;
  // Reset form
  resolveModal.form.action = 'sync_to_system';
  resolveModal.form.note = '';
  resolveModal.visible = true;
}

async function submitResolve() {
  try {
    resolveModal.loading = true;
    await resolveStockDiscrepancy(resolveModal.id, resolveModal.form);
    message.success('处理成功');
    resolveModal.visible = false;
    gridApi.reload();
  } catch (error) {
    console.error(error);
  } finally {
    resolveModal.loading = false;
  }
}

onMounted(() => {
  // Grid auto-loads
});
</script>

<template>
  <Page auto-content-height title="库存同步差异">
    <Grid>
      <template #toolbar_buttons>
        <Space>
          <AButton 
            type="primary" 
            :loading="syncLoading"
            @click="handleSyncAll"
          >
            <SyncOutlined /> 同步所有仓库
          </AButton>
        </Space>
      </template>

      <template #diff_slot="{ row }">
        <span :class="row.diff_qty > 0 ? 'text-red-500 font-bold' : 'text-blue-500 font-bold'">
          {{ row.diff_qty > 0 ? '+' : '' }}{{ row.diff_qty }}
        </span>
      </template>

      <template #status_slot="{ row }">
        <Tag :color="row.status === 'pending' ? 'warning' : (row.status === 'resolved' ? 'success' : 'default')">
          {{ row.status === 'pending' ? '待处理' : (row.status === 'resolved' ? '已解决' : '已忽略') }}
        </Tag>
      </template>

      <template #action_slot="{ row }">
        <AButton 
          v-if="row.status === 'pending'"
          type="link" 
          size="small" 
          @click="handleResolve(row)"
        >
          处理差异
        </AButton>
      </template>
    </Grid>

    <!-- 处理差异弹窗 -->
    <Modal
      v-model:open="resolveModal.visible"
      title="处理库存差异"
      :confirm-loading="resolveModal.loading"
      @ok="submitResolve"
    >
      <Form layout="vertical">
        <div class="mb-4">
          <span class="font-bold">SKU:</span> {{ resolveModal.sku }}
        </div>
        
        <Form.Item label="处理方式" required>
          <Radio.Group v-model:value="resolveModal.form.action">
            <Radio value="sync_to_system" class="block mb-2">
              以平台为准 (更新系统库存)
            </Radio>
            <Radio value="sync_to_platform" class="block mb-2">
              以系统为准 (更新平台库存)
            </Radio>
            <Radio value="ignore" class="block">
              忽略本次差异
            </Radio>
          </Radio.Group>
        </Form.Item>

        <Form.Item label="备注">
          <Input.TextArea 
            v-model:value="resolveModal.form.note" 
            :rows="3" 
            placeholder="请输入处理备注..."
          />
        </Form.Item>
      </Form>
    </Modal>
  </Page>
</template>

