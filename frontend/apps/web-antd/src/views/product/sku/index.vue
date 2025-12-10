<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { onMounted, ref } from 'vue';
import { Button as AButton, Popconfirm, message, Space, Tag, Input } from 'ant-design-vue';
import { EditOutlined, DeleteOutlined, EyeOutlined, SearchOutlined } from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import { useRouter } from 'vue-router';
import type { Sku } from '#/api/core/product';
import SkuFilter from './components/SkuFilter.vue';
import BatchOperations from './components/BatchOperations.vue';

const router = useRouter();
const searchValue = ref('');
const filters = ref<any>({});

// --- Grid Config ---
const gridOptions: VxeGridProps = {
  keepSource: true,
  height: 'auto',
  // 启用自适应行高
  autoResize: true,
  pagerConfig: {
    enabled: true,
    pageSize: 20,
    pageSizes: [10, 20, 50, 100],
  },
  columns: [
    { type: 'checkbox', width: 50, fixed: 'left' },
    { type: 'seq', width: 50, fixed: 'left' },
    { 
      field: 'sku', 
      title: 'SKU编码', 
      width: 180, 
      fixed: 'left', 
      sortable: true,
      slots: { default: 'sku_slot' } 
    },
    { 
      field: 'spu_code', 
      title: 'SPU编码', 
      width: 180,
      sortable: true,
      slots: { default: 'spu_code_slot' }
    },
    { 
      field: 'feature_code', 
      title: '特征码', 
      minWidth: 250,
      showOverflow: true,
    },
    { field: 'product_name', title: '产品名称', minWidth: 200, showOverflow: true },
    { field: 'category_name', title: '分类', width: 120 },
    { 
      field: 'brand_model', 
      title: '品牌/车型', 
      width: 150,
      formatter: ({ row }) => `${row.brand || '-'}/${row.model || '-'}`
    },
    { 
      field: 'attributes_display', 
      title: '属性组合', 
      minWidth: 250,
      // 重要：允许换行和自适应高度
      showOverflow: false, // 关闭溢出隐藏，允许内容撑开
      showHeaderOverflow: true,
      slots: { default: 'attributes_slot' }
    },
    { 
      field: 'stock_quantity', 
      title: '库存', 
      width: 100,
      align: 'center',
      slots: { default: 'stock_slot' }
    },
    { 
      field: 'is_active', 
      title: '状态', 
      width: 80, 
      align: 'center',
      slots: { default: 'status_slot' }
    },
    { field: 'created_at', title: '创建时间', width: 160 },
    {
      title: '操作',
      width: 200,
      fixed: 'right',
      slots: { default: 'action_slot' }
    }
  ],
  // 使用模拟数据，避免API调用错误
  data: [
    {
      sku: '101120501DWD',
      feature_code: 'HL-CHE-SIL-07-13-D-WB',
      spu_code: 'HL-CHE-SIL-07-13', // 添加spu_code
      product_name: '雪佛兰Silverado前大灯',
      category_name: '前大灯',
      brand: '雪佛兰',
      model: 'Silverado',
      attributes: {
        position: '左侧',
        color: '黑色',
        material: 'ABS塑料',
        voltage: '12V',
      },
      attributes_display: 'position:左侧, color:黑色, material:ABS塑料, voltage:12V',
      stock_quantity: 150,
      is_active: true,
      created_at: '2024-01-15 10:30:00',
      product_id: 1,
    },
    {
      sku: '101120501DRD',
      feature_code: 'HL-CHE-SIL-07-13-D-RD',
      spu_code: 'HL-CHE-SIL-07-13',
      product_name: '雪佛兰Silverado前大灯',
      category_name: '前大灯',
      brand: '雪佛兰',
      model: 'Silverado',
      attributes: {
        position: '右侧',
        color: '红色',
        material: 'ABS塑料',
        voltage: '12V',
      },
      attributes_display: 'position:右侧, color:红色, material:ABS塑料, voltage:12V',
      stock_quantity: 120,
      is_active: true,
      created_at: '2024-01-15 10:35:00',
      product_id: 1,
    },
    {
      sku: '102130602PWD',
      feature_code: 'TL-BMW-3ER-05-11-2P-WD',
      spu_code: 'TL-BMW-3ER-05-11',
      product_name: '宝马3系尾灯',
      category_name: '后尾灯',
      brand: '宝马',
      model: '3系',
      attributes: {
        position: '对装',
        color: '白色',
        material: 'PC塑料',
        voltage: '12V',
      },
      attributes_display: 'position:对装, color:白色, material:PC塑料, voltage:12V',
      stock_quantity: 80,
      is_active: true,
      created_at: '2024-01-16 14:20:00',
      product_id: 2,
    },
    {
      sku: '103140703CHR',
      feature_code: 'BM-MB-CLA-12-18-CH-R',
      spu_code: 'BM-MB-CLA-12-18',
      product_name: '奔驰CLA保险杠',
      category_name: '保险杠',
      brand: '奔驰',
      model: 'CLA',
      attributes: {
        position: '右侧',
        color: '镀铬',
        material: 'PP塑料',
        voltage: 'N/A',
      },
      attributes_display: 'position:右侧, color:镀铬, material:PP塑料, voltage:N/A',
      stock_quantity: 45,
      is_active: false,
      created_at: '2024-01-17 09:15:00',
      product_id: 3,
    },
    {
      sku: '104150804BLK',
      feature_code: 'MR-TOY-CAM-07-13-BLK',
      spu_code: 'MR-TOY-CAM-07-13',
      product_name: '丰田凯美瑞后视镜',
      category_name: '后视镜',
      brand: '丰田',
      model: '凯美瑞',
      attributes: {
        position: '左侧',
        color: '黑色',
        material: 'ABS塑料',
        heating: '有',
      },
      attributes_display: 'position:左侧, color:黑色, material:ABS塑料, heating:有',
      stock_quantity: 200,
      is_active: true,
      created_at: '2024-01-18 11:45:00',
      product_id: 4,
    },
    // 添加一个包含更多属性的测试SKU
    {
      sku: '105160905MULTI',
      feature_code: 'ENG-FRD-FOC-12-18-MULTI',
      spu_code: 'ENG-FRD-FOC-12-18',
      product_name: '福特福克斯发动机总成',
      category_name: '发动机',
      brand: '福特',
      model: '福克斯',
      attributes: {
        position: '前置',
        displacement: '1.6L',
        fuel_type: '汽油',
        power: '125马力',
        torque: '159牛米',
        transmission: '手动6速',
        emission_standard: '国六',
        warranty: '3年10万公里',
      },
      attributes_display: 'position:前置, displacement:1.6L, fuel_type:汽油, power:125马力, torque:159牛米, transmission:手动6速, emission_standard:国六, warranty:3年10万公里',
      stock_quantity: 5,
      is_active: true,
      created_at: '2024-01-19 14:30:00',
      product_id: 5,
    },
  ],
  toolbarConfig: {
    refresh: true,
    zoom: true,
    custom: true,
    slots: { buttons: 'toolbar_buttons' }
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

// --- Handlers ---

function handleSearch() {
  // 简单提示
  message.info('搜索功能（模拟数据）');
}

function handleReset() {
  searchValue.value = '';
  filters.value = {};
  message.info('筛选已重置');
}

// 处理筛选
function handleFilterChange(newFilters: any) {
  filters.value = newFilters;
  message.info(`筛选条件已更新: ${JSON.stringify(newFilters)}`);
}

// 处理快速搜索
function handleQuickSearch(value: string) {
  searchValue.value = value;
  message.info(`快速搜索: ${value}`);
}

function handleView(row: Sku) {
  router.push(`/product/sku/detail/${row.sku}`);
}

function handleEdit(row: Sku) {
  // For now, redirect to SPU edit page with variant focus
  router.push(`/product/spu/edit/${row.product_id}?variant=${row.sku}`);
}

async function handleDelete(row: Sku) {
  try {
    // TODO: Implement delete SKU API
    // await deleteSkuApi(row.sku);
    message.success('删除成功');
    gridApi.query();
  } catch (e) {
    // Error handled
  }
}

async function handleToggleStatus(row: Sku) {
  try {
    // TODO: Implement toggle status API
    // await toggleSkuStatusApi(row.sku);
    message.success(`SKU ${row.sku} 状态已切换`);
    gridApi.query();
  } catch (e) {
    console.error('切换状态失败:', e);
    message.error('操作失败');
  }
}

// 导出功能
function handleExport() {
  message.info('导出功能待实现');
}

// 批量操作
const selectedRows = ref<Sku[]>([]);

function handleSelectionChange({ records }: { records: Sku[] }) {
  selectedRows.value = records;
}

function handleBatchEnable() {
  if (selectedRows.value.length === 0) {
    message.warning('请先选择要操作的SKU');
    return;
  }
  message.info(`批量启用 ${selectedRows.value.length} 个SKU（功能待实现）`);
}

function handleBatchDisable() {
  if (selectedRows.value.length === 0) {
    message.warning('请先选择要操作的SKU');
    return;
  }
  message.info(`批量停用 ${selectedRows.value.length} 个SKU（功能待实现）`);
}

function handleBatchExport() {
  if (selectedRows.value.length === 0) {
    message.warning('请先选择要导出的SKU');
    return;
  }
  message.info(`批量导出 ${selectedRows.value.length} 个SKU（功能待实现）`);
}

function handleClearSelection() {
  selectedRows.value = [];
  // 简化清除选择状态，避免类型错误
  try {
    // 尝试使用VxeTable的标准方法清除选择
    const grid = (gridApi as any).$refs?.gridRef;
    if (grid && grid.clearCheckboxRow) {
      grid.clearCheckboxRow();
    }
  } catch (error) {
    console.log('清除选择状态时出错:', error);
  }
}

// 获取属性显示名称（中文化）
function getAttributeDisplayName(key: string): string {
  const nameMap: Record<string, string> = {
    position: '位置',
    color: '颜色',
    material: '材质',
    voltage: '电压',
    heating: '加热',
    size: '尺寸',
    weight: '重量',
    power: '功率',
    displacement: '排量',
    fuel_type: '燃油类型',
    torque: '扭矩',
    transmission: '变速箱',
    emission_standard: '排放标准',
    warranty: '质保',
    // 可以继续添加更多映射
  };
  return nameMap[key] || key;
}

// 获取属性文本颜色
function getAttributeColor(key: string): string {
  const colorMap: Record<string, string> = {
    position: '#1890ff',      // 蓝色
    color: '#52c41a',         // 绿色
    material: '#fa8c16',      // 橙色
    voltage: '#722ed1',       // 紫色
    heating: '#f5222d',       // 红色
    size: '#13c2c2',          // 青色
    weight: '#2f54eb',        // 深蓝
    power: '#eb2f96',         // 粉色
    displacement: '#fa541c',  // 火山红
    fuel_type: '#faad14',     // 金色
    torque: '#a0d911',        // 酸橙绿
    transmission: '#1890ff',  // 蓝色
    emission_standard: '#52c41a', // 绿色
    warranty: '#fa8c16',      // 橙色
  };
  
  return colorMap[key] || '#333';
}

// 根据属性键名获取Tag颜色（保留但不再使用）
function getAttributeTagColor(key: string): string {
  const colorMap: Record<string, string> = {
    position: 'blue',
    color: 'green',
    material: 'orange',
    voltage: 'purple',
    heating: 'red',
    size: 'cyan',
    weight: 'geekblue',
    power: 'magenta',
    displacement: 'volcano',
    fuel_type: 'gold',
    torque: 'lime',
    transmission: 'processing',
    emission_standard: 'success',
    warranty: 'warning',
  };
  
  // 确保返回有效的颜色字符串
  const color = colorMap[key.toLowerCase()];
  return color || 'default';
}

onMounted(() => {
  // Initial load
  gridApi.query();
});
</script>

<template>
  <Page auto-content-height title="SKU管理">
    <!-- 高级筛选组件 -->
    <SkuFilter 
      class="mb-4"
      @filter-change="handleFilterChange"
      @search="handleQuickSearch"
    />

    <!-- 批量操作组件 -->
    <BatchOperations 
      :selected-rows="selectedRows"
      @batch-enable="handleBatchEnable"
      @batch-disable="handleBatchDisable"
      @batch-export="handleBatchExport"
      @clear-selection="handleClearSelection"
    />

    <!-- 数据表格 -->
    <Grid @checkbox-all="handleSelectionChange" @checkbox-change="handleSelectionChange">
      <template #toolbar_buttons>
        <div class="flex items-center gap-2">
          <Input
            v-model:value="searchValue"
            placeholder="搜索SKU编码、特征码、SPU编码、产品名称..."
            style="width: 300px"
            @press-enter="handleSearch"
          >
            <template #suffix>
              <SearchOutlined @click="handleSearch" />
            </template>
          </Input>
          <AButton @click="handleSearch">
            搜索
          </AButton>
          <AButton @click="handleReset">
            重置
          </AButton>
          <AButton type="primary" @click="handleExport">
            导出全部
          </AButton>
        </div>
      </template>

      <template #sku_slot="{ row }">
        <span class="font-mono font-bold text-primary cursor-pointer hover:underline" @click="handleView(row)">
          {{ row.sku }}
        </span>
      </template>

      <template #spu_code_slot="{ row }">
        <div class="flex items-center">
          <span class="font-mono text-blue-600 font-semibold cursor-pointer hover:underline hover:text-blue-800 transition-colors" 
                @click="router.push(`/product/spu/detail/${row.product_id || ''}`)"
                :title="`点击查看SPU详情: ${row.spu_code}`">
            {{ row.spu_code }}
          </span>
          <span v-if="row.spu_code" class="ml-1 text-xs text-gray-400" title="标准产品单元编码">
            📦
          </span>
        </div>
      </template>
      
      <template #attributes_slot="{ row }">
        <div class="attribute-multiline-container">
          <template v-if="row.attributes && typeof row.attributes === 'object'">
            <template v-for="(entry, index) in Object.entries(row.attributes)" :key="entry[0]">
              <div 
                class="attribute-line"
                :class="{ 'has-divider': index < Object.keys(row.attributes).length - 1 }"
              >
                <div class="attribute-item">
                  <span class="attribute-label">{{ getAttributeDisplayName(entry[0]) }}:</span>
                  <span class="attribute-value" :style="{ color: getAttributeColor(entry[0]) }">
                    {{ entry[1] }}
                  </span>
                </div>
              </div>
            </template>
          </template>
          <template v-else-if="row.attributes_display">
            <!-- 兼容旧格式 -->
            <div class="attribute-line">
              <span class="text-gray-600">{{ row.attributes_display }}</span>
            </div>
          </template>
          <template v-else>
            <div class="attribute-line">
              <span class="text-gray-400">-</span>
            </div>
          </template>
        </div>
      </template>
      
      <template #stock_slot="{ row }">
        <Tag :color="row.stock_quantity > 0 ? 'success' : 'error'">
          {{ row.stock_quantity || 0 }}
        </Tag>
      </template>

      <template #status_slot="{ row }">
        <Tag 
          :color="row.is_active ? 'success' : 'error'" 
          class="cursor-pointer"
          @click="handleToggleStatus(row)"
        >
          {{ row.is_active ? '启用' : '停用' }}
        </Tag>
      </template>

      <template #action_slot="{ row }">
        <Space>
          <AButton type="link" size="small" @click="handleView(row)">
            <EyeOutlined /> 详情
          </AButton>
          <AButton type="link" size="small" @click="handleEdit(row)">
            <EditOutlined /> 编辑
          </AButton>
          <Popconfirm title="确定删除该SKU?" @confirm="handleDelete(row)">
            <AButton type="link" size="small" danger>
              <DeleteOutlined /> 删除
            </AButton>
          </Popconfirm>
        </Space>
      </template>
    </Grid>
  </Page>
</template>

<style scoped>
.attribute-multiline-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
  /* 确保容器能撑开高度 */
  min-height: 40px;
  height: auto;
}

.attribute-line {
  display: flex;
  align-items: center;
  min-height: 22px;
  position: relative;
  /* 确保每行有固定高度 */
  height: 22px;
}

/* 间隔线样式 - 底部边框 */
.attribute-line.has-divider::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(0, 0, 0, 0.08) 20%, 
    rgba(0, 0, 0, 0.08) 80%, 
    transparent 100%
  );
}

.attribute-item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  height: 100%;
}

.attribute-label {
  font-size: 12px;
  color: #666;
  min-width: 50px;
  text-align: right;
  line-height: 20px;
  font-weight: 500;
}

.attribute-value {
  font-size: 12px;
  font-weight: 500;
  line-height: 20px;
  height: 20px;
  /* 文本颜色由getAttributeColor函数控制 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 60px;
}

/* 优化表格行高 - 使用VxeTable自动行高 */
/* 属性列自适应高度 */
:deep(.vxe-table--body .vxe-body--column[data-field="attributes_display"]) {
  vertical-align: top;
  padding-top: 8px;
  padding-bottom: 8px;
  /* 允许内容撑开单元格 */
  height: auto !important;
  min-height: 40px;
}

/* 确保表格行能自适应高度 */
:deep(.vxe-body--row) {
  height: auto !important;
}

/* 单元格内容容器 */
:deep(.vxe-body--column .vxe-cell) {
  height: auto !important;
  min-height: 40px;
  display: flex;
  align-items: flex-start;
}

.attribute-tag {
  transition: all 0.2s ease;
  border-radius: 4px;
}

.attribute-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 优化表格行悬停效果 */
:deep(.vxe-body--row.row--hover) {
  background-color: #f8fafc !important;
}

/* 优化固定列样式 */
:deep(.vxe-table--fixed-left .vxe-body--column) {
  background-color: white;
}

:deep(.vxe-table--fixed-right .vxe-body--column) {
  background-color: white;
}
</style>
