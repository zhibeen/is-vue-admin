<script setup lang="ts">
/**
 * 发货单详情页面 - 重构版
 * 采用组件化架构，提升代码可维护性
 */
import { Card, Spin, Modal, message, Tabs } from 'ant-design-vue';
import { onMounted, ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  getShipmentDetail,
  updateShipment,
  confirmShipment,
  generateContracts,
  type Shipment,
} from '#/api/logistics/shipment';
import {
  getPurchaseItems,
  recalculatePurchaseItems,
} from '#/api/logistics/purchase-item';

// 导入子组件
import ShipmentHeader from './components/ShipmentHeader.vue';
import OverviewTab from './components/OverviewTab.vue';
import GoodsTab from './components/GoodsTab.vue';
import PurchaseTab from './components/PurchaseTab.vue';
import LogisticsTab from './components/LogisticsTab.vue';
import LogisticsServicesPanel from './components/LogisticsServicesPanel.vue';
import WarehouseTab from './components/WarehouseTab.vue';
import FinanceTab from './components/FinanceTab.vue';
import DocumentsTab from './components/DocumentsTab.vue';
import VouchersTab from './components/VouchersTab.vue';
import HistoryTab from './components/HistoryTab.vue';
import AddPurchaseModal from './components/AddPurchaseModal.vue';
import ImportPurchaseModal from './components/ImportPurchaseModal.vue';

const route = useRoute();
const router = useRouter();

// 状态管理
const shipmentId = computed(() => Number(route.params.id));
const shipment = ref<Shipment | null>(null);
const purchaseItems = ref<any[]>([]);
const loading = ref(false);
const loadingPurchaseItems = ref(false);
const activeTab = ref('overview');

// 编辑模式
const isEditing = ref(false);
const editForm = ref<any>({});
const saving = ref(false);

// Modal显示状态
const showAddModal = ref(false);
const showImportModal = ref(false);

// 加载详情
async function loadDetail() {
  try {
    loading.value = true;
    shipment.value = await getShipmentDetail(shipmentId.value);
    await loadPurchaseItems();
  } catch (error: any) {
    message.error(error.message || '加载详情失败');
  } finally {
    loading.value = false;
  }
}

// 加载采购明细
async function loadPurchaseItems() {
  try {
    loadingPurchaseItems.value = true;
    const response = await getPurchaseItems(shipmentId.value);
    purchaseItems.value = response || [];
  } catch (error: any) {
    message.error('加载采购明细失败');
    purchaseItems.value = [];
  } finally {
    loadingPurchaseItems.value = false;
  }
}

// 返回列表
function handleBack() {
  router.push('/logistics/shipment');
}

// 进入编辑模式
function handleEdit() {
  if (shipment.value?.status !== 'draft') {
    message.warning('只有草稿状态的发货单才能编辑');
    return;
  }
  
  editForm.value = {
    consignee_name: shipment.value.consignee_name,
    consignee_address: shipment.value.consignee_address,
    consignee_country: shipment.value.consignee_country,
    logistics_provider: shipment.value.logistics_provider,
    tracking_no: shipment.value.tracking_no,
    shipping_method: shipment.value.shipping_method,
    total_packages: shipment.value.total_packages,
    total_gross_weight: shipment.value.total_gross_weight,
    total_net_weight: shipment.value.total_net_weight,
    total_volume: shipment.value.total_volume,
    notes: shipment.value.notes,
  };
  
  isEditing.value = true;
}

// 保存编辑
async function handleSave() {
  try {
    saving.value = true;
    await updateShipment(shipmentId.value, editForm.value);
    message.success('保存成功');
    isEditing.value = false;
    await loadDetail();
  } catch (error: any) {
    message.error(error.message || '保存失败');
  } finally {
    saving.value = false;
  }
}

// 取消编辑
function handleCancelEdit() {
  Modal.confirm({
    title: '确认取消',
    content: '取消后未保存的修改将丢失，是否继续？',
    onOk: () => {
      isEditing.value = false;
      editForm.value = {};
    },
  });
}

// 确认发货单
function handleConfirm() {
  Modal.confirm({
    title: '确认发货单',
    content: '确认后发货单将不能再修改，是否继续？',
    async onOk() {
      try {
        await confirmShipment(shipmentId.value);
        message.success('确认成功');
        loadDetail();
      } catch (error: any) {
        message.error(error.message || '确认失败');
      }
    },
  });
}

// 生成交付合同
function handleGenerateContracts() {
  Modal.confirm({
    title: '生成交付合同',
    content: '将按供应商拆分生成交付合同，是否继续？',
    async onOk() {
      try {
        await generateContracts(shipmentId.value);
        message.success('生成合同成功');
        loadDetail();
      } catch (error: any) {
        message.error(error.message || '生成合同失败');
      }
    },
  });
}

// 添加采购明细
function handleAddPurchaseItem() {
  if (shipment.value?.status !== 'draft') {
    message.warning('只有草稿状态的发货单才能添加采购明细');
    return;
  }
  showAddModal.value = true;
}

// 打开批量导入
function handleOpenImport() {
  if (shipment.value?.status !== 'draft') {
    message.warning('只有草稿状态的发货单才能批量导入');
    return;
  }
  showImportModal.value = true;
}

// 重新计算商品明细
async function handleRecalculate() {
  Modal.confirm({
    title: '确认重新计算',
    content: '此操作将基于当前采购明细重新计算商品明细，是否继续？',
    onOk: async () => {
      try {
        await recalculatePurchaseItems(shipmentId.value);
        message.success('商品明细重新计算完成');
        await loadDetail();
      } catch (error: any) {
        message.error(error.message || '重新计算失败');
      }
    },
  });
}

// Modal成功回调
async function handleModalSuccess() {
  await loadPurchaseItems();
  await loadDetail();
}

// 切换Tab
function handleSwitchTab(tabKey: string) {
  activeTab.value = tabKey;
}

// 挂载时加载
onMounted(() => {
  loadDetail();
});
</script>

<template>
  <div class="p-4">
    <Spin :spinning="loading">
      <!-- 顶部标题栏 -->
      <ShipmentHeader
        :shipment="shipment"
        :is-editing="isEditing"
        :saving="saving"
        @back="handleBack"
        @edit="handleEdit"
        @save="handleSave"
        @cancel-edit="handleCancelEdit"
        @confirm="handleConfirm"
        @generate-contracts="handleGenerateContracts"
      />

      <!-- Tab标签页 -->
      <Card class="mt-4" :bordered="true">
        <Tabs v-model:activeKey="activeTab" type="card" size="large">
          <!-- 概览Tab -->
          <Tabs.TabPane key="overview">
            <template #tab>
              <span class="flex items-center gap-2">
                概览
              </span>
            </template>
            <OverviewTab
              :shipment="shipment"
              :is-editing="isEditing"
              :edit-form="editForm"
              @switch-tab="handleSwitchTab"
              @confirm="handleConfirm"
              @generate-contracts="handleGenerateContracts"
            />
          </Tabs.TabPane>

          <!-- 商品明细Tab -->
          <Tabs.TabPane key="goods">
            <template #tab>
              <span class="flex items-center gap-2">
                商品明细
              </span>
            </template>
            <GoodsTab
              :shipment="shipment"
              :purchase-items="purchaseItems"
            />
          </Tabs.TabPane>

          <!-- 采购明细Tab -->
          <Tabs.TabPane key="purchase">
            <template #tab>
              <span class="flex items-center gap-2">
                采购明细
              </span>
            </template>
            <PurchaseTab
              :shipment="shipment"
              :purchase-items="purchaseItems"
              :loading="loadingPurchaseItems"
              @add="handleAddPurchaseItem"
              @import="handleOpenImport"
              @recalculate="handleRecalculate"
            />
          </Tabs.TabPane>

          <!-- 物流跟踪Tab -->
          <Tabs.TabPane key="logistics">
            <template #tab>
              <span class="flex items-center gap-2">
                物流跟踪
              </span>
            </template>
            <LogisticsTab
              :shipment="shipment"
              :is-editing="isEditing"
              :edit-form="editForm"
            />
          </Tabs.TabPane>

          <!-- 物流服务Tab -->
          <Tabs.TabPane key="logistics-services">
            <template #tab>
              <span class="flex items-center gap-2">
                物流服务
              </span>
            </template>
            <LogisticsServicesPanel :shipment-id="shipmentId" />
          </Tabs.TabPane>

          <!-- 仓库信息Tab -->
          <Tabs.TabPane key="warehouse">
            <template #tab>
              <span class="flex items-center gap-2">
                仓库信息
              </span>
            </template>
            <WarehouseTab :shipment="shipment" />
          </Tabs.TabPane>

          <!-- 物流成本Tab -->
          <Tabs.TabPane key="finance">
            <template #tab>
              <span class="flex items-center gap-2">
                物流成本
              </span>
            </template>
            <FinanceTab :shipment="shipment" />
          </Tabs.TabPane>

          <!-- 关联单据Tab -->
          <Tabs.TabPane key="documents">
            <template #tab>
              <span class="flex items-center gap-2">
                关联单据
              </span>
            </template>
            <DocumentsTab
              :shipment="shipment"
              @generate-contracts="handleGenerateContracts"
            />
          </Tabs.TabPane>

          <!-- 凭证管理Tab -->
          <Tabs.TabPane key="vouchers">
            <template #tab>
              <span class="flex items-center gap-2">
                凭证管理
              </span>
            </template>
            <VouchersTab 
              :shipment-id="shipmentId" 
              :shipment-no="shipment?.shipment_no"
            />
          </Tabs.TabPane>

          <!-- 操作日志Tab -->
          <Tabs.TabPane key="history">
            <template #tab>
              <span class="flex items-center gap-2">
                操作日志
              </span>
            </template>
            <HistoryTab
              :shipment="shipment"
              :is-editing="isEditing"
              :edit-form="editForm"
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </Spin>

    <!-- 添加采购明细Modal -->
    <AddPurchaseModal
      v-model:visible="showAddModal"
      :shipment-id="shipmentId"
      :shipment-status="shipment?.status"
      @success="handleModalSuccess"
    />

    <!-- 批量导入Modal -->
    <ImportPurchaseModal
      v-model:visible="showImportModal"
      @success="handleModalSuccess"
    />
  </div>
</template>

<style scoped>
/* Ant Design 组件深度样式调整 */
:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  width: 140px;
}
</style>
