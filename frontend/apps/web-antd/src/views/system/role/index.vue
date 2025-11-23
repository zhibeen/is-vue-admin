<script lang="ts" setup>
import { ref, onMounted, nextTick } from 'vue';
import { 
  Layout, 
  LayoutSider, 
  LayoutContent, 
  Card, 
  Tabs, 
  TabPane, 
  Button,
  Modal,
  Skeleton
} from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import { SafetyCertificateOutlined } from '@ant-design/icons-vue';
import { getRolesApi, deleteRoleApi, type RoleItem } from '#/api/core/system';
import { message } from 'ant-design-vue';

// Components
import RoleList from './components/RoleList.vue';
import RoleUserTable from './components/RoleUserTable.vue';
import FunctionalPermTable from './components/FunctionalPermTable.vue';
import DataPermTable from './components/DataPermTable.vue';
import FieldPermTable from './components/FieldPermTable.vue';
import RoleUpsertModal from './components/RoleUpsertModal.vue';

// Refs
const roleListRef = ref();
const upsertModalRef = ref();
const funcPermRef = ref();
const dataPermRef = ref();
const fieldPermRef = ref();

// State
const loading = ref(false);
const roles = ref<RoleItem[]>([]);
const activeRole = ref<RoleItem | null>(null);
const activeTab = ref('users');
const isDirty = ref(false);

// Actions
const fetchRoles = async () => {
  loading.value = true;
  try {
    roles.value = await getRolesApi();
    // Select first if none selected
    if (!activeRole.value && roles.value.length > 0) {
      handleSelectRole(roles.value[0]);
    } else if (activeRole.value) {
      // Refresh active role data
      const current = roles.value.find(r => r.id === activeRole.value?.id);
      if (current) activeRole.value = current;
    }
  } finally {
    loading.value = false;
  }
};

const handleSelectRole = (role: RoleItem) => {
  if (isDirty.value) {
    Modal.confirm({
      title: '未保存更改',
      content: '您有未保存的更改，切换角色将丢失这些更改。是否继续？',
      onOk: () => {
        isDirty.value = false;
        switchRole(role);
      }
    });
  } else {
    switchRole(role);
  }
};

const switchRole = (role: RoleItem) => {
  activeRole.value = null; // Trigger skeleton
  nextTick(() => {
    activeRole.value = role;
    // Reset tab state if needed, or keep current tab
  });
};

const handleDeleteRole = (role: RoleItem) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除角色 ${role.name} 吗？`,
    onOk: async () => {
      await deleteRoleApi(role.id);
      message.success('删除成功');
      if (activeRole.value?.id === role.id) {
        activeRole.value = null;
      }
      fetchRoles();
    }
  });
};

const handleSave = async () => {
  let success = false;
  if (activeTab.value === 'permissions' && funcPermRef.value) {
    success = await funcPermRef.value.save();
  } else if (activeTab.value === 'data' && dataPermRef.value) {
    success = await dataPermRef.value.save();
  } else if (activeTab.value === 'field' && fieldPermRef.value) {
    success = await fieldPermRef.value.save();
  }
  
  if (success) {
    // Refresh roles to get updated permissions in list/memory
    fetchRoles(); 
  }
};

const handleDirty = (val: boolean) => {
  isDirty.value = val;
};

// Modal Handlers
const handleCreate = () => upsertModalRef.value?.open('create');
const handleEdit = (role: RoleItem) => upsertModalRef.value?.open('edit', role);
const handleCopy = (role: RoleItem) => upsertModalRef.value?.open('create', role);

onMounted(() => {
  fetchRoles();
});
</script>

<template>
  <Page content-class="h-[calc(100vh-150px)] overflow-hidden">
    <Layout class="h-full bg-transparent gap-4">
    
      <!-- Left Sidebar -->
      <LayoutSider width="280" class="bg-transparent" theme="light">
        <Card :body-style="{ padding: '0', height: '100%' }" class="h-full border-none shadow-sm">
          <RoleList 
            :roles="roles" 
            :active-role-id="activeRole?.id"
            :loading="loading"
            @select="handleSelectRole"
            @refresh="fetchRoles"
            @create="handleCreate"
            @edit="handleEdit"
            @copy="handleCopy"
            @delete="handleDeleteRole"
          />
        </Card>
      </LayoutSider>

      <!-- Right Content -->
      <LayoutContent class="bg-transparent">
        <Card v-if="activeRole" :body-style="{ padding: '0', height: '100%', display: 'flex', flexDirection: 'column' }" class="h-full border-none shadow-sm">
          <!-- Header -->
          <div class="px-6 py-5 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
            <h2 class="text-xl font-bold flex items-center">
              {{ activeRole.name }}
            </h2>
            <Button 
              v-if="isDirty" 
              type="primary" 
              @click="handleSave"
              class="shadow-sm"
            >
              保存修改
            </Button>
          </div>

          <!-- Tabs -->
          <div class="flex-1 overflow-hidden flex flex-col">
            <Tabs v-model:activeKey="activeTab" class="px-6 h-full flex flex-col [&_.ant-tabs-content]:flex-1 [&_.ant-tabs-content]:h-full">
              
              <TabPane key="users" tab="角色用户" class="h-full">
                <RoleUserTable :role="activeRole" />
              </TabPane>

              <TabPane key="permissions" tab="功能权限" class="h-full">
                <FunctionalPermTable ref="funcPermRef" :role="activeRole" @dirty="handleDirty" />
              </TabPane>

              <TabPane key="data" tab="数据权限" class="h-full">
                <DataPermTable ref="dataPermRef" :role="activeRole" @dirty="handleDirty" />
              </TabPane>

              <TabPane key="field" tab="字段权限" class="h-full">
                <FieldPermTable ref="fieldPermRef" :role="activeRole" @dirty="handleDirty" />
              </TabPane>

            </Tabs>
          </div>
        </Card>
        
        <!-- Empty/Loading State -->
        <Card v-else :body-style="{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }" class="h-full border-none shadow-sm">
          <div v-if="loading" class="p-8 w-full">
             <Skeleton active />
          </div>
          <div v-else class="text-center">
            <SafetyCertificateOutlined class="text-6xl mb-4 text-gray-200" />
            <p class="text-gray-400">请选择一个角色</p>
          </div>
        </Card>
      </LayoutContent>
    </Layout>

    <RoleUpsertModal ref="upsertModalRef" @success="fetchRoles" />
  </Page>
</template>
