<template>
  <div class="py-4">
    <div class="mb-4 bg-blue-50 p-3 rounded border border-blue-100 flex items-center">
      <InfoCircleOutlined class="text-blue-500 mr-2" />
      <span class="text-gray-600 text-sm">
        启用仓库后，第三方仓库数据将同步到本系统。系统会自动在“仓库管理”中创建对应的本地仓库映射。
      </span>
    </div>

    <!-- 筛选栏 -->
    <div class="mb-4 flex gap-2">
      <InputSearch 
        v-model:value="searchText"
        placeholder="搜索仓库名称/代码" 
        style="width: 250px" 
        @search="loadData"
        allowClear
      />
      <Button @click="loadData">刷新</Button>
    </div>

    <Table 
      :columns="columns" 
      :data-source="filteredData" 
      :loading="loading"
      row-key="id"
      size="middle"
      :pagination="{ pageSize: 20 }"
    >
      <!-- 三方信息 -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'local_info'">
          <div v-if="record.is_active" class="flex items-center text-blue-600">
             <HomeOutlined class="mr-1"/>
             {{ record.service_warehouse_name || '自动生成中...' }}
          </div>
          <span v-else class="text-gray-400">-</span>
        </template>

        <template v-if="column.key === 'is_active'">
          <Switch 
            v-model:checked="record.is_active" 
            :loading="record.toggleLoading"
            checked-children="已启用" 
            un-checked-children="未启用"
            @change="(val) => handleToggle(val, record)"
          />
        </template>

        <template v-if="column.key === 'action'">
          <Button type="link" :disabled="!record.is_active">编辑映射</Button>
        </template>
      </template>
    </Table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { Table, Switch, InputSearch, Button, message } from 'ant-design-vue';
import { InfoCircleOutlined, HomeOutlined } from '@ant-design/icons-vue';
import { requestClient } from '#/api/request';

const props = defineProps<{ serviceId: number }>();
const emit = defineEmits(['refresh']);

const loading = ref(false);
const dataSource = ref<any[]>([]);
const searchText = ref('');

const columns = [
  { title: '第三方仓库名称', dataIndex: 'name', width: 200 },
  { title: '第三方仓库代码', dataIndex: 'code', width: 150 },
  { title: '国家/地区', dataIndex: 'country_code', width: 100 },
  { title: '系统仓库名称', key: 'local_info', width: 200 },
  { title: '启用', key: 'is_active', width: 120, align: 'center' as const },
  { title: '操作', key: 'action', width: 100 }
];

const loadData = async () => {
  if (!props.serviceId) return;
  loading.value = true;
  try {
    const res = await requestClient.get(`/v1/third-party/services/${props.serviceId}/warehouses`);
    dataSource.value = res;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

// 前端简单筛选
const filteredData = computed(() => {
  if (!searchText.value) return dataSource.value;
  const key = searchText.value.toLowerCase();
  return dataSource.value.filter(item => 
    item.name.toLowerCase().includes(key) || 
    item.code.toLowerCase().includes(key)
  );
});

const handleToggle = async (checked: boolean | string | number, record: any) => {
  const isChecked = Boolean(checked);
  try {
    record.toggleLoading = true;
    await requestClient.put(`/v1/third-party/services/${props.serviceId}/warehouses/${record.id}/toggle`, {
      is_active: isChecked
    });
    
    message.success(isChecked ? '仓库已启用' : '仓库已禁用');
    // 重新加载以获取最新的本地仓库映射信息
    await loadData(); 
    emit('refresh');
  } catch (e: any) {
    record.is_active = !isChecked; // 回滚状态
    message.error(e.message || '操作失败');
  } finally {
    record.toggleLoading = false;
  }
};

watch(() => props.serviceId, loadData);
onMounted(loadData);

defineExpose({ loadData });
</script>

