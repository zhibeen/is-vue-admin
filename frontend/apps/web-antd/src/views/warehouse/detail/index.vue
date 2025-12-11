<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { Page } from '@vben/common-ui';
import { Tabs, TabPane, Descriptions, DescriptionsItem, Tag, Card, Button } from 'ant-design-vue';
import { getWarehouseDetail, type Warehouse } from '#/api/warehouse';

const route = useRoute();
const id = Number(route.params.id);
const warehouse = ref<Warehouse | null>(null);
const activeKey = ref('basic');

const categoryMap: Record<string, string> = { physical: '实体仓', virtual: '虚拟仓' };
const locationMap: Record<string, string> = { domestic: '国内', overseas: '海外' };
const statusColorMap: Record<string, string> = {
  active: 'green',
  planning: 'blue',
  suspended: 'orange',
  deprecated: 'gray',
  clearing: 'red'
};

async function loadData() {
  if (!id) return;
  try {
    const data = await getWarehouseDetail(id);
    warehouse.value = data;
  } catch (error) {
    console.error(error);
  }
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <Page title="仓库详情">
    <template #extra>
      <Button @click="$router.back()">返回</Button>
    </template>
    
    <div class="p-4" v-if="warehouse">
      <Card :bordered="false" class="mb-4">
        <Descriptions title="基本信息" bordered>
          <DescriptionsItem label="编码">{{ warehouse.code }}</DescriptionsItem>
          <DescriptionsItem label="名称">{{ warehouse.name }}</DescriptionsItem>
          <DescriptionsItem label="形态">
            <Tag color="blue">{{ categoryMap[warehouse.category] || warehouse.category }}</Tag>
          </DescriptionsItem>
          <DescriptionsItem label="地理位置">{{ locationMap[warehouse.location_type] || warehouse.location_type }}</DescriptionsItem>
          <DescriptionsItem label="状态">
            <Tag :color="statusColorMap[warehouse.status]">{{ warehouse.status }}</Tag>
          </DescriptionsItem>
          <DescriptionsItem label="币种">{{ warehouse.currency }}</DescriptionsItem>
          <DescriptionsItem label="负责人">{{ warehouse.contact_person || '-' }}</DescriptionsItem>
          <DescriptionsItem label="联系电话">{{ warehouse.contact_phone || '-' }}</DescriptionsItem>
          <DescriptionsItem label="地址" :span="3">{{ warehouse.address || '-' }}</DescriptionsItem>
        </Descriptions>
      </Card>
      
      <Card :bordered="false">
        <Tabs v-model:activeKey="activeKey">
          <TabPane key="basic" tab="详细配置">
             <div class="p-4">
               <p v-if="warehouse.category === 'virtual'">
                 <!-- 虚拟仓特定配置，如子仓关联 -->
                 <strong>关联子仓ID:</strong> {{ warehouse.child_warehouse_ids || '无' }}
               </p>
               <p v-if="warehouse.api_config">
                 <!-- 三方仓特定配置 -->
                 <strong>API配置:</strong> {{ warehouse.api_config }}
               </p>
               <p v-if="!warehouse.api_config && warehouse.category === 'physical'">
                 暂无额外配置
               </p>
             </div>
          </TabPane>
          <TabPane key="location" tab="库位管理" v-if="warehouse.category === 'physical'">
            <!-- 替换原有的占位文本 -->
            <LocationList :warehouse-id="id" />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  </Page>
</template>

