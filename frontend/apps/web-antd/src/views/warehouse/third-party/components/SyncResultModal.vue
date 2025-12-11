<template>
  <Modal
    :open="visible"
    title="同步仓库清单"
    width="800px"
    @cancel="handleCancel"
    :footer="null"
  >
    <div class="mb-4">
      <Button type="primary" :loading="syncLoading" @click="handleSync">
        <template #icon><ReloadOutlined /></template>
        开始同步
      </Button>
      <span class="ml-2 text-gray-500">从 {{ service?.name }} 拉取最新仓库列表</span>
    </div>

    <Table
      :columns="columns"
      :data-source="remoteWarehouses"
      :loading="loading"
      size="small"
      :pagination="false"
      :scroll="{ y: 400 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <Badge v-if="record.is_bound" status="success" :text="`已绑定: ${record.local_warehouse_name}`" />
          <Badge v-else status="warning" text="未绑定" />
        </template>
        
        <template v-if="column.key === 'action'">
          <Space v-if="!record.is_bound">
            <Popconfirm
              title="确定要自动创建对应的本地仓库吗？"
              @confirm="handleBind(record, 'create_new')"
            >
              <Button type="link" size="small">生成本地仓</Button>
            </Popconfirm>
            <!-- 预留: 绑定现有 -->
            <!-- <Button type="link" size="small">绑定现有</Button> -->
          </Space>
        </template>
      </template>
    </Table>
  </Modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { Modal, Button, Table, Badge, Space, Popconfirm, message } from 'ant-design-vue';
import { ReloadOutlined } from '@ant-design/icons-vue';
import { 
  syncRemoteWarehouses, 
  bindRemoteWarehouse,
  type ThirdPartyService, 
  type RemoteWarehouse 
} from '#/api/warehouse/third_party';

const props = defineProps<{ 
  visible: boolean;
  service?: ThirdPartyService;
}>();

const emit = defineEmits(['update:visible', 'success']);

const loading = ref(false);
const syncLoading = ref(false);
const remoteWarehouses = ref<RemoteWarehouse[]>([]);

const columns = [
  { title: '远程代码', dataIndex: 'remote_code', width: 120 },
  { title: '远程名称', dataIndex: 'remote_name' },
  { title: '状态', key: 'status' },
  { title: '操作', key: 'action', width: 150 }
];

const handleSync = async () => {
  if (!props.service) return;
  syncLoading.value = true;
  loading.value = true;
  try {
    const list = await syncRemoteWarehouses(props.service.id);
    remoteWarehouses.value = list;
    message.success(`同步成功，获取到 ${list.length} 个仓库`);
  } catch (e) {
    console.error(e);
  } finally {
    syncLoading.value = false;
    loading.value = false;
  }
};

const handleBind = async (record: RemoteWarehouse, action: 'create_new' | 'bind_existing') => {
  if (!props.service) return;
  try {
    await bindRemoteWarehouse(props.service.id, {
      remote_code: record.remote_code,
      remote_name: record.remote_name,
      action
    });
    message.success('绑定成功');
    // 刷新列表状态
    handleSync();
    emit('success'); // 通知父组件可能需要刷新
  } catch (e) {
    console.error(e);
  }
};

watch(() => props.visible, (val) => {
  if (val) {
    remoteWarehouses.value = []; // 打开时清空，等待用户点同步，或者自动同步
    handleSync(); // 自动同步一次
  }
});

const handleCancel = () => {
  emit('update:visible', false);
};
</script>

