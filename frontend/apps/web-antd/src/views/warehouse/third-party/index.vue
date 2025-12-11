<template>
  <div class="p-4">
    <div class="mb-4 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold">三方服务管理</h1>
        <p class="text-gray-500">配置第三方物流服务商授权 (4PX, Winit等)</p>
      </div>
      <Button type="primary" @click="handleCreate">
        <template #icon><PlusOutlined /></template>
        新增授权
      </Button>
    </div>

    <Table
      :columns="columns"
      :data-source="services"
      :loading="loading"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'provider'">
          <Tag color="blue">{{ record.provider_code.toUpperCase() }}</Tag>
        </template>
        
        <template v-if="column.key === 'status'">
          <Badge
            :status="record.status === 'connected' ? 'success' : 'error'"
            :text="record.status === 'connected' ? '已连接' : '未连接'"
          />
        </template>

        <template v-if="column.key === 'is_active'">
          <Switch 
            v-model:checked="record.is_active" 
            @change="handleToggleActive(record)"
            :loading="toggleLoading[record.id]"
          />
        </template>

        <template v-if="column.key === 'action'">
          <Space>
            <Button type="link" @click="handleEdit(record)">编辑</Button>
            <Button type="link" @click="handleTest(record)">测试</Button>
            <Button type="link" @click="handleSync(record)">同步仓库</Button>
            <Button type="link" danger @click="handleDelete(record)">删除</Button>
          </Space>
        </template>
      </template>
    </Table>

    <!-- 授权弹窗 -->
    <ServiceModal
      v-model:visible="modalVisible"
      :record="currentRecord"
      :mode="modalMode"
      @success="loadData"
    />

    <!-- 同步结果弹窗 -->
    <SyncResultModal
      v-model:visible="syncVisible"
      :service="currentService"
      @success="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { Table, Button, Tag, Badge, Space, Modal, message, Switch } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';
import { 
  getThirdPartyServices, 
  deleteThirdPartyService, 
  updateThirdPartyService,
  testThirdPartyConnection,
  type ThirdPartyService 
} from '#/api/warehouse/third_party';
import ServiceModal from './components/ServiceModal.vue';
import SyncResultModal from './components/SyncResultModal.vue';

const loading = ref(false);
const services = ref<ThirdPartyService[]>([]);
const modalVisible = ref(false);
const syncVisible = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const currentRecord = ref<ThirdPartyService>();
const currentService = ref<ThirdPartyService>();
const toggleLoading = reactive<Record<number, boolean>>({});

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '别名', dataIndex: 'name' },
  { title: '代码', dataIndex: 'code' },
  { title: '供应商', key: 'provider', dataIndex: 'provider_code' },
  { title: 'API地址', dataIndex: 'api_url' },
  { title: '状态', key: 'status', dataIndex: 'status' },
  { title: '启用', key: 'is_active', dataIndex: 'is_active', width: 100 },
  { title: '上次同步', dataIndex: 'last_sync_time' },
  { title: '操作', key: 'action', width: 300 }
];

const loadData = async () => {
  loading.value = true;
  try {
    const data = await getThirdPartyServices();
    services.value = data;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const handleCreate = () => {
  currentRecord.value = undefined;
  modalMode.value = 'create';
  modalVisible.value = true;
};

import { useRouter } from 'vue-router';

const router = useRouter();

// ... existing code ...

const handleEdit = (record: ThirdPartyService) => {
  router.push({ name: 'ThirdPartyServiceDetail', params: { id: record.id } });
};

const handleTest = async (record: ThirdPartyService) => {
  try {
    message.loading({ content: '正在测试连接...', key: 'test', duration: 0 });
    
    const result = await testThirdPartyConnection({
      provider_code: record.provider_code,
      api_url: record.api_url,
      app_key: record.app_key || '',
      app_secret: '' // 密码不传，后端应该从数据库读取
    });
    
    message.destroy('test');
    
    if (result.success) {
      message.success('连接测试成功！');
    } else {
      message.error(`连接测试失败：${result.message || '未知错误'}`);
    }
  } catch (error: any) {
    message.destroy('test');
    message.error(`连接测试失败：${error.message || '未知错误'}`);
  }
};

const handleSync = (record: ThirdPartyService) => {
  currentService.value = record;
  syncVisible.value = true;
};

const handleToggleActive = async (record: ThirdPartyService) => {
  try {
    toggleLoading[record.id] = true;
    await updateThirdPartyService(record.id, { is_active: !record.is_active });
    message.success(record.is_active ? '已禁用' : '已启用');
    loadData();
  } catch (error: any) {
    message.error(error.message || '操作失败');
    // 回滚状态
    record.is_active = !record.is_active;
  } finally {
    toggleLoading[record.id] = false;
  }
};

const handleDelete = (record: ThirdPartyService) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除授权 "${record.name}" 吗？关联的仓库映射关系也将失效。`,
    okType: 'danger',
    onOk: async () => {
      await deleteThirdPartyService(record.id);
      message.success('删除成功');
      loadData();
    }
  });
};

onMounted(loadData);
</script>

