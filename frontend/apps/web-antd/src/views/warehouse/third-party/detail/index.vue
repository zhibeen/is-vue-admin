<template>
  <Page>
    <!-- 头部信息卡片 -->
    <div class="bg-white p-4 rounded-lg shadow-sm mb-4">
      <div class="flex justify-between items-start">
        <div class="flex gap-4">
          <Avatar :size="64" shape="square" class="bg-blue-100 text-blue-600 font-bold text-xl">
            {{ serviceInfo?.provider_code?.substring(0, 2).toUpperCase() }}
          </Avatar>
          <div>
            <h1 class="text-xl font-bold mb-2">{{ serviceInfo?.name }}</h1>
            <Space :size="20" class="text-gray-500">
              <span>服务商: {{ serviceInfo?.provider_code?.toUpperCase() }}</span>
              <span>
                同步状态: 
                <Badge :status="serviceInfo?.status === 'connected' ? 'success' : 'error'" 
                       :text="serviceInfo?.status === 'connected' ? '正常同步' : '异常'" />
              </span>
              <span>上次同步: {{ serviceInfo?.last_sync_time || '-' }}</span>
            </Space>
          </div>
        </div>
        <Space>
          <Button type="primary" ghost @click="handleSync" :loading="syncLoading">
            <template #icon><SyncOutlined /></template>
            全量拉取刷新
          </Button>
          <Button @click="router.back()">返回</Button>
        </Space>
      </div>
    </div>

    <!-- 核心 Tabs 区域 -->
    <div class="bg-white rounded-lg shadow-sm min-h-[500px]">
      <Tabs v-model:activeKey="activeTab" class="px-4">
        <TabPane key="warehouse" tab="仓库设置">
          <WarehouseList :service-id="serviceId" @refresh="loadServiceInfo" />
        </TabPane>
        
        <TabPane key="sku" tab="SKU配对">
           <SkuMappingList :service-id="serviceId" />
        </TabPane>
        
        <TabPane key="config" tab="授权配置">
          <div class="p-8 text-center text-gray-400">授权配置功能移至列表页编辑...</div>
        </TabPane>
      </Tabs>
    </div>
  </Page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Avatar, Space, Button, Tabs, TabPane, Badge, message } from 'ant-design-vue';
import { SyncOutlined } from '@ant-design/icons-vue';
import { Page } from '@vben/common-ui';
import { getThirdPartyService, syncThirdPartyWarehouses } from '#/api/warehouse/third_party';

// 子组件引入
import WarehouseList from './components/WarehouseList.vue';
import SkuMappingList from './components/SkuMappingList.vue';

const route = useRoute();
const router = useRouter();
const serviceId = Number(route.params.id);

const serviceInfo = ref<any>({});
const activeTab = ref('warehouse');
const syncLoading = ref(false);

const loadServiceInfo = async () => {
  if (!serviceId) return;
  try {
    serviceInfo.value = await getThirdPartyService(serviceId);
  } catch (e) {
    console.error(e);
  }
};

const handleSync = async () => {
  try {
    syncLoading.value = true;
    await syncThirdPartyWarehouses(serviceId);
    message.success('同步指令已发送，数据刷新中...');
    await loadServiceInfo();
    // 强制刷新子组件: 简单方式是通过key, 或者让子组件监听 props
    // 这里子组件 WarehouseList 监听了 serviceId，但 serviceId 没变。
    // 我们可以在 WarehouseList 里 expose 一个 refresh 方法，或者这里加个 key
  } finally {
    syncLoading.value = false;
  }
};

onMounted(loadServiceInfo);
</script>

