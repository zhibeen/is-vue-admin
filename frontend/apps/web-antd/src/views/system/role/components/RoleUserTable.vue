<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue';
import { 
  Input, 
  Button, 
  Table,
  Tag,
  Modal,
  Transfer,
  message 
} from 'ant-design-vue';
import { SearchOutlined } from '@ant-design/icons-vue';
import { 
  getRoleUsersApi, 
  addRoleUsersApi, 
  removeRoleUserApi, 
  getUsersApi,
  type UserItem,
  type RoleItem
} from '#/api/core/system';

const props = defineProps<{
  role: RoleItem;
}>();

const roleUsers = ref<UserItem[]>([]);
const userSearchText = ref('');
const loading = ref(false);

const userColumns = [
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '昵称', dataIndex: 'nickname', key: 'nickname' }, 
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '状态', dataIndex: 'is_active', key: 'is_active' },
  { title: '操作', key: 'action', width: 100 },
];

const fetchRoleUsers = async () => {
  loading.value = true;
  try {
    const params = { page: 1, per_page: 100, q: userSearchText.value };
    const res: any = await getRoleUsersApi(props.role.id, params);
    
    let items = [];
    if (res && Array.isArray(res.items)) {
      items = res.items;
    } else if (res && res.data && Array.isArray(res.data.items)) {
      items = res.data.items;
    } else if (res && res.data && Array.isArray(res.data)) {
      items = res.data;
    }
    
    roleUsers.value = items;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const handleRemoveUser = (user: UserItem) => {
  Modal.confirm({
    title: '确认移除',
    content: `确定要将用户 ${user.username} 从角色中移除吗？`,
    onOk: async () => {
      await removeRoleUserApi(props.role.id, user.id);
      message.success('移除成功');
      fetchRoleUsers();
    }
  });
};

// --- Add User Logic ---
const userSelectVisible = ref(false);
const transferDataSource = ref<any[]>([]);
const transferTargetKeys = ref<string[]>([]);
const transferSelectedKeys = ref<string[]>([]);

const handleOpenAddUser = async () => {
  userSelectVisible.value = true;
  // Fetch ALL users
  const res = await getUsersApi({ page: 1, per_page: 0 });
  const currentIds = roleUsers.value.map(u => u.id.toString());
  
  transferDataSource.value = res.items.map(u => ({
    key: u.id.toString(),
    title: u.nickname ? `${u.username}(${u.nickname})` : u.username,
  }));
    
  transferTargetKeys.value = currentIds;
  transferSelectedKeys.value = [];
};

const handleAddUserSubmit = async () => {
  try {
    const newTargetIds = transferTargetKeys.value.map(k => parseInt(k));
    const initialIds = roleUsers.value.map(u => u.id);
    
    const addedIds = newTargetIds.filter(id => !initialIds.includes(id));
    const removedIds = initialIds.filter(id => !newTargetIds.includes(id));
    
    if (addedIds.length > 0) {
        await addRoleUsersApi(props.role.id, addedIds);
    }
    
    if (removedIds.length > 0) {
        const removePromises = removedIds.map(uid => removeRoleUserApi(props.role.id, uid));
        await Promise.all(removePromises);
    }
    
    if (addedIds.length > 0 || removedIds.length > 0) {
      message.success('保存成功');
      fetchRoleUsers();
    } else {
      message.info('未做更改');
    }

    userSelectVisible.value = false;
  } catch (e) {
    console.error(e);
    message.error('操作失败，请重试');
  }
};

watch(() => props.role.id, () => {
  userSearchText.value = '';
  fetchRoleUsers();
}, { immediate: true });

</script>

<template>
  <div class="h-full flex flex-col py-4">
    <div class="flex justify-between mb-4">
      <div class="space-x-2">
        <Button type="primary" @click="handleOpenAddUser">添加用户</Button>
        <!-- <Button>批量移除</Button> -->
      </div>
      <Input v-model:value="userSearchText" placeholder="用户名/真实姓名" class="w-64" @pressEnter="fetchRoleUsers">
        <template #suffix><SearchOutlined class="text-gray-400"/></template>
      </Input>
    </div>
    
    <div class="flex-1 overflow-y-auto">
      <Table 
        :columns="userColumns" 
        :data-source="roleUsers" 
        size="middle" 
        :pagination="false"
        :loading="loading"
        class="border border-gray-100 dark:border-gray-800 rounded-md"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <Button type="link" danger size="small" @click="handleRemoveUser(record as UserItem)">移除</Button>
          </template>
          <template v-if="column.key === 'is_active'">
            <Tag :color="record.is_active ? 'green' : 'red'">{{ record.is_active ? '启用' : '禁用' }}</Tag>
          </template>
        </template>
        <template #emptyText>
          <div class="text-center py-8 text-gray-400">暂无用户数据</div>
        </template>
      </Table>
    </div>

    <Modal v-model:open="userSelectVisible" title="管理角色用户" @ok="handleAddUserSubmit" width="650px">
      <div class="flex justify-center py-4">
        <Transfer
          v-model:target-keys="transferTargetKeys"
          v-model:selected-keys="transferSelectedKeys"
          :data-source="transferDataSource"
          :titles="['未分配用户', '已分配用户']"
          :render="item => item.title"
          :list-style="{
            width: '280px',
            height: '350px',
          }"
          show-search
          :locale="{ itemUnit: '项', itemsUnit: '项', notFoundContent: '列表为空', searchPlaceholder: '请输入搜索内容' }"
        />
      </div>
    </Modal>
  </div>
</template>

