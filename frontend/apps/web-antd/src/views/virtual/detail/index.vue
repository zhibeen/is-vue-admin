<template>
  <div class="p-4">
    <PageWrapper title="虚拟仓详情" content="查看和管理虚拟仓的详细信息及分配策略">
      <div class="mb-6">
        <a-card title="基本信息" class="mb-4">
          <a-descriptions :column="3" bordered>
            <a-descriptions-item label="虚拟仓编码">{{ warehouseInfo?.code }}</a-descriptions-item>
            <a-descriptions-item label="虚拟仓名称">{{ warehouseInfo?.name }}</a-descriptions-item>
            <a-descriptions-item label="仓库形态">
              {{ warehouseInfo?.category === 'virtual' ? '虚拟仓' : '实体仓' }}
            </a-descriptions-item>
            <a-descriptions-item label="地理位置">
              {{ warehouseInfo?.location_type === 'domestic' ? '国内' : '海外' }}
            </a-descriptions-item>
            <a-descriptions-item label="管理模式">
              {{ warehouseInfo?.ownership_type === 'self' ? '自营' : '第三方' }}
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getStatusColor(warehouseInfo?.status)">
                {{ getStatusText(warehouseInfo?.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="业务类型">
              {{ getBusinessTypeText(warehouseInfo?.business_type) }}
            </a-descriptions-item>
            <a-descriptions-item label="计价币种">{{ warehouseInfo?.currency }}</a-descriptions-item>
            <a-descriptions-item label="时区">{{ warehouseInfo?.timezone }}</a-descriptions-item>
            <a-descriptions-item label="创建时间">{{ warehouseInfo?.created_at }}</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 分配策略管理 -->
        <a-card title="分配策略管理" class="mb-4">
          <template #extra>
            <a-space>
              <a-button type="primary" size="small" @click="handleCreatePolicy">
                <template #icon><PlusOutlined /></template>
                新建策略
              </a-button>
              <a-button size="small" @click="handleCalculateStock">
                <template #icon><CalculatorOutlined /></template>
                计算库存
              </a-button>
            </a-space>
          </template>

          <div class="mb-4">
            <a-alert
              message="分配策略说明"
              description="分配策略用于控制虚拟仓的库存分配规则，支持四层策略体系：单品级 > 分组级 > 品类级 > 仓库级"
              type="info"
              show-icon
            />
          </div>

          <div class="bg-white">
            <VbenVxeGrid ref="policyGridRef" :grid-options="policyGridOptions" />
          </div>
        </a-card>

        <!-- 库存计算结果 -->
        <a-card v-if="stockResult" title="库存计算结果">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="总物理库存">{{ stockResult.total_physical }}</a-descriptions-item>
            <a-descriptions-item label="总可用库存">{{ stockResult.total_available }}</a-descriptions-item>
            <a-descriptions-item label="总已分配库存">{{ stockResult.total_allocated }}</a-descriptions-item>
          </a-descriptions>

          <div class="mt-4">
            <h4 class="mb-2">SKU明细</h4>
            <VbenVxeGrid :grid-options="stockGridOptions" />
          </div>
        </a-card>
      </div>
    </PageWrapper>

    <!-- 分配策略弹窗 -->
    <AllocationPolicyModal
      v-model:visible="policyModalVisible"
      :virtual-warehouse-id="warehouseId"
      :record="currentPolicy"
      :mode="policyModalMode"
      @success="handlePolicyModalSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { PageWrapper } from '@vben/layouts';
import { VbenVxeGrid } from '#/adapter/vxe-table';
import { PlusOutlined, CalculatorOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import AllocationPolicyModal from '../components/AllocationPolicyModal.vue';
import { 
  getVirtualWarehouseList, 
  calculateVirtualStock,
  getPolicyList,
  deletePolicy,
  type VirtualWarehouse,
  type AllocationPolicy,
  type VirtualStockResult
} from '#/api/virtual';
import type { VxeGridProps, VxeGridInstance } from '#/adapter/vxe-table';

const route = useRoute();
const warehouseId = computed(() => parseInt(route.params.id as string));

// 虚拟仓信息
const warehouseInfo = ref<VirtualWarehouse | null>(null);

// 分配策略相关
const policyGridRef = ref<VxeGridInstance>();
const policyModalVisible = ref(false);
const policyModalMode = ref<'create' | 'edit'>('create');
const currentPolicy = ref<AllocationPolicy | null>(null);

// 库存计算结果
const stockResult = ref<VirtualStockResult | null>(null);

// 加载虚拟仓信息
const loadWarehouseInfo = async () => {
  try {
    const res = await getVirtualWarehouseList({ page: 1, per_page: 1, q: warehouseId.value.toString() });
    if (res.items.length > 0) {
      warehouseInfo.value = res.items[0];
    }
  } catch (error) {
    console.error('获取虚拟仓信息失败:', error);
    message.error('获取虚拟仓信息失败');
  }
};

// 分配策略表格配置
const policyGridOptions = reactive<VxeGridProps>({
  border: true,
  stripe: true,
  showOverflow: true,
  keepSource: true,
  height: 'auto',
  columns: [
    { type: 'seq', width: 60, title: '序号' },
    { 
      field: 'policy_mode', 
      title: '策略模式', 
      width: 100,
      formatter: ({ cellValue }) => {
        return cellValue === 'override' ? '覆盖' : '继承';
      }
    },
    { 
      field: 'priority', 
      title: '优先级', 
      width: 80,
      formatter: ({ cellValue }) => `P${cellValue}`
    },
    { 
      field: 'source_warehouse_id', 
      title: '源仓库', 
      width: 120,
      formatter: ({ cellValue }) => cellValue || '全局'
    },
    { 
      field: 'category_id', 
      title: '品类', 
      width: 120,
      formatter: ({ cellValue }) => cellValue || '-'
    },
    { 
      field: 'warehouse_product_group_id', 
      title: 'SKU分组', 
      width: 120,
      formatter: ({ cellValue }) => cellValue || '-'
    },
    { 
      field: 'sku', 
      title: 'SKU', 
      width: 120,
      formatter: ({ cellValue }) => cellValue || '-'
    },
    { 
      field: 'ratio', 
      title: '分配比例', 
      width: 100,
      formatter: ({ cellValue }) => cellValue ? `${(cellValue * 100).toFixed(1)}%` : '-'
    },
    { 
      field: 'fixed_amount', 
      title: '固定数量', 
      width: 100,
      formatter: ({ cellValue }) => cellValue || '-'
    },
    { field: 'created_at', title: '创建时间', width: 180 },
    {
      title: '操作',
      width: 150,
      fixed: 'right',
      slots: {
        default: ({ row }: { row: AllocationPolicy }) => {
          return (
            <div class="flex gap-2">
              <a-button
                type="link"
                size="small"
                onClick={() => handleEditPolicy(row)}
              >
                <EditOutlined /> 编辑
              </a-button>
              <a-button
                type="link"
                size="small"
                danger
                onClick={() => handleDeletePolicy(row)}
              >
                <DeleteOutlined /> 删除
              </a-button>
            </div>
          );
        }
      }
    }
  ],
  data: [],
  pagerConfig: {
    enabled: true,
    pageSize: 10,
    pageSizes: [10, 20, 50],
    layouts: ['PrevJump', 'PrevPage', 'Number', 'NextPage', 'NextJump', 'Sizes', 'Total']
  },
  toolbarConfig: {
    refresh: true,
    refreshOptions: { code: 'query' },
    custom: true
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const params = {
            page: page.currentPage,
            per_page: page.pageSize
          };
          const res = await getPolicyList(warehouseId.value, params);
          return {
            result: res.items,
            page: { total: res.total }
          };
        } catch (error) {
          console.error('获取分配策略失败:', error);
          message.error('获取分配策略失败');
          return { result: [], page: { total: 0 } };
        }
      }
    }
  }
});

// 库存表格配置
const stockGridOptions = reactive<VxeGridProps>({
  border: true,
  stripe: true,
  showOverflow: true,
  keepSource: true,
  height: '300',
  columns: [
    { type: 'seq', width: 60, title: '序号' },
    { field: 'sku', title: 'SKU', width: 120 },
    { field: 'physical_quantity', title: '物理库存', width: 100 },
    { field: 'available_quantity', title: '可用库存', width: 100 },
    { field: 'allocated_quantity', title: '已分配库存', width: 100 },
    { field: 'source_warehouse_id', title: '源仓库', width: 120 },
    { 
      field: 'allocation_ratio', 
      title: '分配比例', 
      width: 100,
      formatter: ({ cellValue }) => cellValue ? `${(cellValue * 100).toFixed(1)}%` : '-'
    }
  ],
  data: stockResult.value?.items || []
});

// 加载分配策略
const loadPolicies = () => {
  policyGridRef.value?.commitProxy('query');
};

// 创建分配策略
const handleCreatePolicy = () => {
  currentPolicy.value = null;
  policyModalMode.value = 'create';
  policyModalVisible.value = true;
};

// 编辑分配策略
const handleEditPolicy = (policy: AllocationPolicy) => {
  currentPolicy.value = policy;
  policyModalMode.value = 'edit';
  policyModalVisible.value = true;
};

// 删除分配策略
const handleDeletePolicy = (policy: AllocationPolicy) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除此分配策略吗？此操作不可恢复。',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deletePolicy(policy.id);
        message.success('删除成功');
        loadPolicies();
      } catch (error) {
        console.error('删除失败:', error);
        message.error('删除失败');
      }
    }
  });
};

// 计算库存
const handleCalculateStock = async () => {
  try {
    const result = await calculateVirtualStock(warehouseId.value);
    stockResult.value = result;
    stockGridOptions.data = result.items;
    message.success('库存计算完成');
  } catch (error) {
    console.error('计算库存失败:', error);
    message.error('计算库存失败');
  }
};

// 策略弹窗成功回调
const handlePolicyModalSuccess = () => {
  policyModalVisible.value = false;
  loadPolicies();
};

// 状态颜色映射
const getStatusColor = (status?: string) => {
  const map: Record<string, string> = {
    planning: 'blue',
    active: 'green',
    suspended: 'orange',
    clearing: 'red',
    deprecated: 'gray'
  };
  return status ? map[status] || 'default' : 'default';
};

// 状态文本映射
const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    planning: '筹备中',
    active: '正常',
    suspended: '暂停',
    clearing: '清退中',
    deprecated: '已废弃'
  };
  return status ? map[status] || status : '-';
};

// 业务类型文本映射
const getBusinessTypeText = (businessType?: string) => {
  const map: Record<string, string> = {
    standard: '标准仓',
    fba: 'FBA仓',
    bonded: '保税仓',
    transit: '中转仓'
  };
  return businessType ? map[businessType] || businessType : '-';
};

onMounted(() => {
  loadWarehouseInfo();
  loadPolicies();
});
</script>
