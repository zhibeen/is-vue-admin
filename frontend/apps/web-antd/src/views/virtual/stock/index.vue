<template>
  <div class="p-4">
    <PageWrapper title="虚拟仓库存计算" content="计算和查看虚拟仓的库存分配情况">
      <div class="mb-6">
        <a-card title="计算配置" class="mb-4">
          <a-form
            ref="formRef"
            :model="formState"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 16 }"
          >
            <a-form-item label="选择虚拟仓" name="virtual_warehouse_id">
              <a-select
                v-model:value="formState.virtual_warehouse_id"
                placeholder="请选择虚拟仓"
                style="width: 300px"
                :options="virtualWarehouseOptions"
                @change="handleVirtualWarehouseChange"
              />
            </a-form-item>

            <a-form-item label="计算时间" name="calc_time">
              <a-date-picker
                v-model:value="formState.calc_time"
                show-time
                placeholder="选择计算时间点"
                style="width: 300px"
              />
              <div class="text-gray-500 text-xs mt-1">
                留空表示使用当前时间计算
              </div>
            </a-form-item>

            <a-form-item :wrapper-col="{ offset: 6, span: 16 }">
              <a-space>
                <a-button type="primary" @click="handleCalculate" :loading="calculating">
                  <template #icon><CalculatorOutlined /></template>
                  开始计算
                </a-button>
                <a-button @click="handleReset">
                  <template #icon><ReloadOutlined /></template>
                  重置
                </a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>

        <!-- 计算结果 -->
        <a-card v-if="stockResult" title="计算结果">
          <template #extra>
            <a-button @click="handleExport">
              <template #icon><DownloadOutlined /></template>
              导出结果
            </a-button>
          </template>

          <div class="mb-6">
            <a-descriptions title="汇总信息" :column="3" bordered>
              <a-descriptions-item label="虚拟仓">
                {{ selectedWarehouse?.name || '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="总物理库存">
                <span class="text-lg font-semibold">{{ stockResult.total_physical }}</span>
              </a-descriptions-item>
              <a-descriptions-item label="总可用库存">
                <span class="text-lg font-semibold text-green-600">{{ stockResult.total_available }}</span>
              </a-descriptions-item>
              <a-descriptions-item label="总已分配库存">
                <span class="text-lg font-semibold text-blue-600">{{ stockResult.total_allocated }}</span>
              </a-descriptions-item>
              <a-descriptions-item label="分配率">
                <span class="text-lg font-semibold">
                  {{ calculateAllocationRate() }}%
                </span>
              </a-descriptions-item>
              <a-descriptions-item label="计算时间">
                {{ new Date().toLocaleString() }}
              </a-descriptions-item>
            </a-descriptions>
          </div>

          <div class="mb-4">
            <h3 class="text-lg font-medium mb-2">库存分布</h3>
            <div class="bg-white">
              <VbenVxeGrid :grid-options="stockGridOptions" />
            </div>
          </div>

          <div>
            <h3 class="text-lg font-medium mb-2">分配策略应用情况</h3>
            <a-table
              :data-source="allocationDetails"
              :columns="allocationColumns"
              :pagination="false"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'policy_type'">
                  <a-tag :color="getPolicyTypeColor(record.policy_type)">
                    {{ record.policy_type }}
                  </a-tag>
                </template>
                <template v-if="column.dataIndex === 'applied_ratio'">
                  {{ (record.applied_ratio * 100).toFixed(1) }}%
                </template>
              </template>
            </a-table>
          </div>
        </a-card>

        <!-- 无结果提示 -->
        <a-card v-else-if="hasCalculated" title="计算结果">
          <a-empty description="未找到符合条件的库存数据" />
        </a-card>
      </div>
    </PageWrapper>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { PageWrapper } from '@vben/layouts';
import { VbenVxeGrid } from '#/adapter/vxe-table';
import { CalculatorOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';
import { 
  getVirtualWarehouseList, 
  calculateVirtualStock,
  type VirtualWarehouse,
  type VirtualStockResult
} from '#/api/virtual';
import type { VxeGridProps } from '#/adapter/vxe-table';
import type { FormInstance } from 'ant-design-vue';

const formRef = ref<FormInstance>();
const calculating = ref(false);
const hasCalculated = ref(false);

// 虚拟仓选项
const virtualWarehouseOptions = ref<{ value: number; label: string }[]>([]);
const selectedWarehouse = ref<VirtualWarehouse | null>(null);

// 表单状态
const formState = reactive({
  virtual_warehouse_id: undefined as number | undefined,
  calc_time: undefined as dayjs.Dayjs | undefined
});

// 库存计算结果
const stockResult = ref<VirtualStockResult | null>(null);

// 加载虚拟仓列表
const loadVirtualWarehouses = async () => {
  try {
    const res = await getVirtualWarehouseList({ page: 1, per_page: 100 });
    virtualWarehouseOptions.value = res.items
      .filter(wh => wh.category === 'virtual')
      .map(wh => ({
        value: wh.id,
        label: `${wh.code} - ${wh.name}`
      }));
  } catch (error) {
    console.error('加载虚拟仓列表失败:', error);
    message.error('加载虚拟仓列表失败');
  }
};

// 虚拟仓选择变化
const handleVirtualWarehouseChange = (value: number) => {
  // TODO: 根据ID获取虚拟仓详情
  selectedWarehouse.value = null;
};

// 计算库存
const handleCalculate = async () => {
  if (!formState.virtual_warehouse_id) {
    message.warning('请选择虚拟仓');
    return;
  }

  calculating.value = true;
  try {
    const result = await calculateVirtualStock(formState.virtual_warehouse_id);
    stockResult.value = result;
    hasCalculated.value = true;
    
    // 更新表格数据
    stockGridOptions.data = result.items;
    
    message.success('库存计算完成');
  } catch (error) {
    console.error('计算库存失败:', error);
    message.error('计算库存失败');
  } finally {
    calculating.value = false;
  }
};

// 重置
const handleReset = () => {
  formRef.value?.resetFields();
  stockResult.value = null;
  hasCalculated.value = false;
  selectedWarehouse.value = null;
};

// 导出结果
const handleExport = () => {
  if (!stockResult.value) {
    message.warning('没有可导出的数据');
    return;
  }
  
  // TODO: 实现导出功能
  message.info('导出功能开发中');
};

// 计算分配率
const calculateAllocationRate = () => {
  if (!stockResult.value || stockResult.value.total_physical === 0) {
    return 0;
  }
  return ((stockResult.value.total_allocated / stockResult.value.total_physical) * 100).toFixed(1);
};

// 库存表格配置
const stockGridOptions = reactive<VxeGridProps>({
  border: true,
  stripe: true,
  showOverflow: true,
  keepSource: true,
  height: '400',
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
    },
    {
      title: '分配状态',
      width: 120,
      slots: {
        default: ({ row }: { row: any }) => {
          const rate = row.allocated_quantity / row.physical_quantity;
          let color = 'green';
          let text = '正常';
          
          if (rate >= 0.9) {
            color = 'red';
            text = '紧张';
          } else if (rate >= 0.7) {
            color = 'orange';
            text = '偏高';
          } else if (rate <= 0.3) {
            color = 'blue';
            text = '充足';
          }
          
          return <a-tag :color="color">{text}</a-tag>;
        }
      }
    }
  ],
  data: []
});

// 分配策略详情
const allocationDetails = ref([
  { policy_type: '单品级', applied_count: 5, applied_ratio: 0.3 },
  { policy_type: '分组级', applied_count: 3, applied_ratio: 0.4 },
  { policy_type: '品类级', applied_count: 8, applied_ratio: 0.2 },
  { policy_type: '仓库级', applied_count: 12, applied_ratio: 0.1 }
]);

// 分配策略表格列
const allocationColumns = [
  { title: '策略类型', dataIndex: 'policy_type', key: 'policy_type' },
  { title: '应用数量', dataIndex: 'applied_count', key: 'applied_count' },
  { title: '应用比例', dataIndex: 'applied_ratio', key: 'applied_ratio' },
  { title: '说明', dataIndex: 'description', key: 'description' }
];

// 获取策略类型颜色
const getPolicyTypeColor = (type: string) => {
  const map: Record<string, string> = {
    '单品级': 'red',
    '分组级': 'orange',
    '品类级': 'blue',
    '仓库级': 'green'
  };
  return map[type] || 'default';
};

onMounted(() => {
  loadVirtualWarehouses();
});
</script>
