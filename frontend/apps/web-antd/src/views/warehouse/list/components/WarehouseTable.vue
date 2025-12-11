<template>
  <Card :bordered="false">
    <Grid>
      <template #category="{ row }">
        <Tag :color="row.category === 'physical' ? 'blue' : 'purple'">
          {{ categoryMap[row.category] || row.category }}
        </Tag>
      </template>
      <template #location="{ row }">
        <Tag :color="row.location_type === 'domestic' ? 'green' : 'red'">
          {{ locationMap[row.location_type] || row.location_type }}
        </Tag>
      </template>
      <template #ownership="{ row }">
        {{ ownershipMap[row.ownership_type] || row.ownership_type }}
      </template>
      <template #status="{ row }">
        <Tag :color="statusColorMap[row.status]">
          {{ statusMap[row.status] || row.status }}
        </Tag>
      </template>
      <template #third_party_info="{ row }">
        <div v-if="row.ownership_type === 'third_party'">
          <div v-if="row.third_party_service_id">
            <div class="text-xs">
              <span class="font-medium">服务商:</span> 
              <span class="font-medium">
                  {{ (row.third_party_service_id && serviceMap[row.third_party_service_id]?.name) || '未知服务商' }}
                </span>
            </div>
            <div v-if="row.third_party_warehouse_id" class="text-xs mt-1">
              <span class="font-medium">仓库:</span> 
              {{ warehouseMap[row.third_party_warehouse_id]?.name || `ID: ${row.third_party_warehouse_id}` }}
            </div>
          </div>
          <div v-else class="text-xs text-gray-400">未配置服务商</div>
        </div>
        <div v-else class="text-xs text-gray-400">-</div>
      </template>
      <template #warehouse_detail="{ row }">
        <div class="warehouse-detail-cell py-1.5">
          
          <!-- 1. 虚拟仓库 -->
          <div v-if="row.category === 'virtual'" class="detail-group virtual">
            <div class="flex items-center flex-wrap gap-2 text-purple-600">
              <div class="flex items-center shrink-0">
                <ClusterOutlined class="mr-1.5" />
                <span class="font-medium">{{ getBusinessTypeLabel(row.business_type) }}</span>
              </div>
              <span v-if="row.child_warehouse_ids && row.child_warehouse_ids.length > 0" class="tag-badge">
                关联 {{ row.child_warehouse_ids.length }} 子仓
              </span>
              <span v-else class="text-gray-400 text-xs">独立虚拟仓</span>
            </div>
          </div>

          <!-- 2. 三方仓库 -->
          <div v-else-if="row.ownership_type === 'third_party'" class="detail-group third-party">
            <div class="flex items-center flex-wrap gap-2 text-blue-600">
              <div class="flex items-center shrink-0">
                <CloudServerOutlined class="mr-1.5" />
                <span class="font-medium">
                  {{ serviceMap[row.third_party_service_id]?.name || '未知服务商' }}
                </span>
              </div>
              <div v-if="row.third_party_warehouse_id" class="text-gray-500 text-xs flex items-center">
                <span class="mx-1">·</span>
                <span>外仓: {{ warehouseMap[row.third_party_warehouse_id]?.name || row.third_party_warehouse_id }}</span>
              </div>
              <div v-else class="text-gray-400 text-xs">未绑定</div>
            </div>
          </div>

          <!-- 3. 自营实体仓库 -->
          <div v-else class="detail-group physical">
            <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
              <!-- 位置类型 -->
              <div class="flex items-center text-emerald-600 shrink-0">
                <EnvironmentOutlined class="mr-1.5" />
                <span class="font-medium">
                  {{ row.location_type === 'domestic' ? '国内' : '海外' }}
                </span>
              </div>
              
              <!-- 容量/体积 (如果存在) -->
              <div v-if="row.capacity || row.max_volume" class="flex items-center text-gray-400 text-xs bg-gray-50 px-1.5 rounded border border-gray-100 shrink-0">
                 <InboxOutlined class="mr-1" />
                 <span>
                   {{ row.capacity ? Math.floor(row.capacity) : '-' }} / {{ row.max_volume ? Math.floor(row.max_volume) + 'm³' : '-' }}
                 </span>
              </div>

              <!-- 地址 (作为补充信息放在后面) -->
              <span v-if="row.address" class="text-gray-500 text-xs break-all">
                {{ row.address }}
              </span>
            </div>
          </div>
          
        </div>
      </template>
      <template #action="{ row }">
        <Space size="small">
          <Button type="link" size="small" @click="() => emit('view-detail', row)">
            <template #icon><EyeOutlined /></template>
            详情
          </Button>
          <Button type="link" size="small" @click="() => emit('edit', row)">
            <template #icon><EditOutlined /></template>
            编辑
          </Button>
          <Button 
            type="link" 
            size="small" 
            danger 
            :disabled="!canDeleteWarehouse(row)"
            @click="() => emit('delete', row)"
          >
            <template #icon><DeleteOutlined /></template>
            删除
          </Button>
        </Space>
      </template>
      
      <!-- 工具栏自定义内容 -->
      <template #toolbar_buttons>
        <Button size="small" @click="() => (gridApi as any).exportData?.()">
          <template #icon><DownloadOutlined /></template>
          导出
        </Button>
        <Button size="small" @click="() => (gridApi as any).toggleFullScreen?.()">
          <template #icon><ExpandOutlined /></template>
          全屏
        </Button>
      </template>
    </Grid>
  </Card>
</template>

<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getWarehouseList, type Warehouse, type WarehouseQuery } from '#/api/warehouse';
import { getThirdPartyServices, getThirdPartyWarehouses, type ThirdPartyService, type ThirdPartyWarehouse } from '#/api/warehouse/third_party';
import { Card, Tag, Button, Space } from 'ant-design-vue';
import { 
  EyeOutlined, EditOutlined, DeleteOutlined, 
  DownloadOutlined, ExpandOutlined,
  CloudServerOutlined,
  EnvironmentOutlined,
  ClusterOutlined,
  InboxOutlined
} from '@ant-design/icons-vue';
import { watch, ref, onMounted } from 'vue';

interface Props {
  searchParams: WarehouseQuery;
}

interface Emits {
  (e: 'view-detail', row: Warehouse): void;
  (e: 'edit', row: Warehouse): void;
  (e: 'delete', row: Warehouse): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 服务商和仓库映射
const serviceMap = ref<Record<number, ThirdPartyService>>({});
const warehouseMap = ref<Record<number, ThirdPartyWarehouse>>({});

// 加载服务商列表
const loadServices = async () => {
  try {
    const services = await getThirdPartyServices();
    serviceMap.value = {};
    services.forEach(service => {
      serviceMap.value[service.id] = service;
    });
  } catch (error) {
    console.error('Failed to load third party services:', error);
  }
};

// 加载特定服务商的仓库列表
const loadWarehousesForService = async (serviceId: number) => {
  try {
    const warehouses = await getThirdPartyWarehouses(serviceId);
    warehouses.forEach(warehouse => {
      warehouseMap.value[warehouse.id] = warehouse;
    });
  } catch (error) {
    console.error(`Failed to load warehouses for service ${serviceId}:`, error);
  }
};

// 组件挂载时加载服务商
onMounted(() => {
  loadServices();
});

// 字典翻译映射
const categoryMap: Record<string, string> = { physical: '实体仓', virtual: '虚拟仓' };
const locationMap: Record<string, string> = { domestic: '国内', overseas: '海外' };
const ownershipMap: Record<string, string> = { self: '自营', third_party: '三方' };
const statusMap: Record<string, string> = { 
  planning: '筹备中', 
  active: '正常', 
  suspended: '暂停', 
  clearing: '清退中', 
  deprecated: '已废弃' 
};
const statusColorMap: Record<string, string> = {
  active: 'green',
  planning: 'blue',
  suspended: 'orange',
  deprecated: 'gray',
  clearing: 'red'
};

// 业务类型标签映射
const businessTypeMap: Record<string, string> = {
  standard: '标准仓',
  fba: 'FBA仓',
  bonded: '保税仓',
  transit: '中转仓',
  sales_channel: '销售渠道',
  planning: '采购计划',
  // 其他业务类型可以继续添加
};

// 获取业务类型标签
const getBusinessTypeLabel = (type: string | undefined): string => {
  return type ? businessTypeMap[type] || type : '未指定';
};

// 获取地理位置信息（虽然模板中直接使用了逻辑，但保留函数以备复用）
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const getLocationInfo = (row: Warehouse): string => {
  if (row.address && row.address.trim()) {
    // 截取地址前20个字符
    return row.address.length > 20 ? row.address.substring(0, 20) + '...' : row.address;
  }
  return row.location_type === 'domestic' ? '国内' : '海外';
};

// 格式化日期（只显示日期部分）
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const formatDate = (dateString: string): string => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch (error) {
    console.error('Date format error:', error);
    return dateString.substring(0, 10); // 简单截取前10位
  }
};

// 判断仓库是否可以删除
const canDeleteWarehouse = (row: Warehouse): boolean => {
  // 只有非活跃状态的仓库可以删除
  return row.status !== 'active';
};

// 定义 Grid 配置
const gridOptions: VxeGridProps<Warehouse> = {
  columns: [
    { field: 'code', title: '仓库编码', width: 180 },
    { field: 'name', title: '仓库名称', minWidth: 120 },
    { 
      field: 'category', 
      title: '形态', 
      width: 80,
      slots: { default: 'category' },
      filters: [
        { label: '实体仓', value: 'physical' },
        { label: '虚拟仓', value: 'virtual' }
      ],
      filterMultiple: false
    },
    { 
      field: 'location_type', 
      title: '地理位置', 
      width: 80,
      slots: { default: 'location' },
      filters: [
        { label: '国内', value: 'domestic' },
        { label: '海外', value: 'overseas' }
      ],
      filterMultiple: false
    },
    { 
      field: 'warehouse_detail', 
      title: '仓库详情', 
      minWidth: 200,
      slots: { default: 'warehouse_detail' }
    },
    { 
      field: 'status', 
      title: '状态', 
      width: 80,
      slots: { default: 'status' },
      filters: [
        { label: '筹备中', value: 'planning' },
        { label: '正常', value: 'active' },
        { label: '暂停', value: 'suspended' },
        { label: '清退中', value: 'clearing' },
        { label: '已废弃', value: 'deprecated' }
      ],
      filterMultiple: true
    },
    { field: 'business_type', title: '业务类型', width: 100 },
    { field: 'currency', title: '币种', width: 70 },
    { field: 'contact_person', title: '负责人', width: 90 },
    { field: 'created_at', title: '创建时间', width: 100, slots: { default: 'created_at' } },
    { title: '操作', width: 150, fixed: 'right', slots: { default: 'action' } },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page, filters }) => {
        console.log('=== WarehouseTable query called ===');
        console.log('1. 表格筛选器 filters:', filters);
        console.log('2. 外部搜索参数 props.searchParams:', props.searchParams);

        // 构建基础参数（先包含所有外部搜索表单的值）
        const params: WarehouseQuery = {
          page: page.currentPage,
          per_page: page.pageSize,
          keyword: props.searchParams.keyword || undefined,
          category: props.searchParams.category || undefined,
          location_type: props.searchParams.location_type || undefined,
          ownership_type: props.searchParams.ownership_type || undefined,
          status: props.searchParams.status || undefined,
        };

        console.log('3. 初始 params (包含外部搜索表单):', params);

        // 如果有表格内置筛选器，则覆盖对应字段
        if (filters) {
          console.log('4. 有表格筛选器，开始处理覆盖...');
          const validKeys = ['category', 'location_type', 'ownership_type', 'status'] as const;
          
          validKeys.forEach((key: any) => {
            const filter = filters[key] as string[] | undefined;
            if (filter && filter.length > 0) {
              (params as any)[key] = filter.join(',');
              console.log(`   - ${key}: 表格筛选器覆盖为`, (params as any)[key]);
            } else {
              console.log(`   - ${key}: 保持外部搜索表单值`, (params as any)[key]);
            }
          });
        }

        console.log('5. 最终API参数:', params);
        console.log('=== 结束 ===');
        
        const result = await getWarehouseList(params);
        
        // 加载三方仓库的详细信息
        const thirdPartyWarehouses = result.items.filter(w => 
          w.ownership_type === 'third_party' && w.third_party_service_id
        );
        
        // 收集需要加载的服务商ID
        const serviceIds = new Set<number>();
        thirdPartyWarehouses.forEach(w => {
          if (w.third_party_service_id) {
            serviceIds.add(w.third_party_service_id);
          }
        });
        
        // 为每个服务商加载仓库列表
        for (const serviceId of serviceIds) {
          await loadWarehousesForService(serviceId);
        }
        
        return result;
      },
    },
  },
  toolbarConfig: {
    custom: true,
    export: true,
    refresh: true,
    zoom: true,
  },
  pagerConfig: {
    enabled: true,
    pageSize: 20,
    pageSizes: [10, 20, 50, 100],
  },
  // 自适应配置
  autoResize: true,
  // 关闭虚拟滚动以支持自动行高
  scrollY: { enabled: false },
  resizeConfig: {
    // minWidth: 800, // 最小宽度
  },
  // 列宽自适应
  columnConfig: {
    resizable: true, // 允许手动调整列宽
  },
};

// 初始化 Grid
const [Grid, gridApi] = useVbenVxeGrid({ 
  gridOptions,
});

// 监听searchParams变化
watch(() => props.searchParams, () => {
  // 当搜索参数变化时，重新加载数据
  console.log('WarehouseTable: searchParams changed, reloading...');
  gridApi.reload();
}, { deep: true });

// 暴露刷新方法
defineExpose({
  reload: () => gridApi.reload(),
});
</script>

<style scoped>
/* 核心容器：增加上下padding防止遮挡 */
.warehouse-detail-cell {
  width: 100%;
  font-size: 13px;
  line-height: 1.5;
}

/* 标题行通用样式 */
.detail-header {
  display: flex;
  align-items: center;
  font-size: 13px;
  line-height: 1.2;
}

/* 内容区域 */
.detail-content {
  font-size: 12px;
  color: #6b7280; /* text-gray-500 */
}

/* 小徽标样式 */
.tag-badge {
  display: inline-block;
  padding: 0 6px;
  border-radius: 4px;
  background-color: #f3f4f6;
  color: #4b5563;
  font-size: 11px;
  border: 1px solid #e5e7eb;
}

/* 信息项 (图标+文字) */
.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-item .icon {
  font-size: 10px;
  color: #9ca3af;
}

/* 颜色工具类 */
.text-purple-600 { color: #9333ea; }
.text-blue-600 { color: #2563eb; }
.text-emerald-600 { color: #059669; }
.text-gray-400 { color: #9ca3af; }
.text-gray-500 { color: #6b7280; }
.text-gray-700 { color: #374151; }
</style>
