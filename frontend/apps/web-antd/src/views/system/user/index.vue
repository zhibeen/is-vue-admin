<script lang="ts" setup>
import { ref, onMounted, reactive } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import {
  getUsersApi, createUserApi, updateUserApi, deleteUserApi, getRolesApi,
  type UserItem, type RoleItem
} from '#/api/core/system';
import { 
  PlusOutlined, DeleteOutlined, ReloadOutlined, 
  SearchOutlined, ExportOutlined 
} from '@ant-design/icons-vue';

// State
const loading = ref(false);
const users = ref<UserItem[]>([]);
const roles = ref<RoleItem[]>([]);

// 搜索表单状态
const searchForm = reactive({
  keyword: '',
  role_id: undefined,
  status: undefined,
  dateRange: []
});

// 分页状态
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
});

// Modal State
const modalVisible = ref(false);
const modalType = ref<'create' | 'edit'>('create');
const formData = reactive({
  id: 0,
  username: '',
  email: '',
  password: '',
  role_ids: [] as number[],
  is_active: true,
});

// Reset Password State
const resetPwdVisible = ref(false);
const resetPwdData = reactive({ id: 0, password: '', username: '' });

// 列定义
const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '用户名', dataIndex: 'username', width: 150 },
  { title: '真实姓名', dataIndex: 'realName', width: 120 }, // 预留字段
  { title: '手机号', dataIndex: 'mobile', width: 120 },     // 预留字段
  { title: '邮箱', dataIndex: 'email', width: 200 },
  { title: '角色', key: 'roles', width: 200 },
  { title: '状态', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', width: 180 },
  { title: '最近登录', key: 'last_login', width: 180 },    // 预留字段
  { title: '操作', key: 'action', fixed: 'right', width: 200 },
];

// Actions
const fetchRoles = async () => {
  roles.value = await getRolesApi();
};

const fetchUsers = async () => {
  loading.value = true;
  try {
    // 这里实际应将 searchForm 参数传给后端
    const res = await getUsersApi({
      page: pagination.current,
      per_page: pagination.pageSize,
      // ...searchForm // 待后端支持过滤参数
    });
    users.value = res.items;
    pagination.total = res.total;
  } finally {
    loading.value = false;
  }
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchUsers();
};

const handleSearch = () => {
  pagination.current = 1;
  fetchUsers();
};

const handleResetSearch = () => {
  searchForm.keyword = '';
  searchForm.role_id = undefined;
  searchForm.status = undefined;
  searchForm.dateRange = [];
  handleSearch();
};

const handleAdd = () => {
  modalType.value = 'create';
  Object.assign(formData, {
    id: 0, username: '', email: '', password: '', role_ids: [], is_active: true
  });
  modalVisible.value = true;
};

const handleEdit = (record: UserItem) => {
  modalType.value = 'edit';
  Object.assign(formData, {
    id: record.id,
    username: record.username,
    email: record.email,
    password: '', // Don't populate password
    role_ids: record.roles.map(r => r.id),
    is_active: record.is_active
  });
  modalVisible.value = true;
};

const handleDelete = (record: UserItem) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除用户 ${record.username} 吗？`,
    onOk: async () => {
      await deleteUserApi(record.id);
      message.success('删除成功');
      fetchUsers();
    }
  });
};

const handleResetPwd = (record: UserItem) => {
  resetPwdData.id = record.id;
  resetPwdData.username = record.username;
  resetPwdData.password = '';
  resetPwdVisible.value = true;
};

const submitResetPwd = async () => {
  if (!resetPwdData.password || resetPwdData.password.length < 6) {
    message.error('密码至少6位');
    return;
  }
  try {
    await updateUserApi(resetPwdData.id, { password: resetPwdData.password });
    message.success('密码重置成功');
    resetPwdVisible.value = false;
  } catch (error) {
    console.error(error);
  }
};

const handleSubmit = async () => {
  try {
    if (!formData.username || !formData.email) {
      message.error('请填写完整信息');
      return;
    }
    if (modalType.value === 'create' && !formData.password) {
      message.error('创建用户必须填写密码');
      return;
    }

    const payload = {
      username: formData.username,
      email: formData.email,
      role_ids: formData.role_ids,
      is_active: formData.is_active,
      password: formData.password || undefined
    };

    if (modalType.value === 'create') {
      await createUserApi(payload as any);
      message.success('创建成功');
    } else {
      await updateUserApi(formData.id, payload);
      message.success('更新成功');
    }
    modalVisible.value = false;
    fetchUsers();
  } catch (error) {
    console.error(error);
  }
};

onMounted(() => {
  fetchRoles();
  fetchUsers();
});
</script>

<template>
  <Page title="用户管理">
    <!-- 搜索区域 -->
    <div class="bg-white p-4 mb-4 rounded shadow-sm">
      <a-form layout="inline" :model="searchForm">
        <a-form-item label="用户状态">
          <a-select v-model:value="searchForm.status" placeholder="请选择" style="width: 120px" allow-clear>
            <a-select-option :value="1">开启</a-select-option>
            <a-select-option :value="0">禁用</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="用户角色">
          <a-select v-model:value="searchForm.role_id" placeholder="请选择角色" style="width: 150px" allow-clear>
            <a-select-option v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="搜索用户">
          <a-input v-model:value="searchForm.keyword" placeholder="用户名/邮箱/姓名" allow-clear style="width: 200px" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <template #icon><SearchOutlined /></template>
              查询
            </a-button>
            <a-button @click="handleResetSearch">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </div>

    <!-- 表格区域 -->
    <div class="bg-white p-4 rounded shadow-sm">
      <div class="mb-4 flex justify-between">
        <a-space>
          <a-button type="primary" @click="handleAdd">
            <template #icon><PlusOutlined /></template>
            添加用户
          </a-button>
          <a-button danger :disabled="true">
             <template #icon><DeleteOutlined /></template>
             批量删除
          </a-button>
        </a-space>
        <a-space>
          <a-button>
             <template #icon><ExportOutlined /></template>
             导出数据
          </a-button>
        </a-space>
      </div>

      <a-table
        :columns="columns"
        :data-source="users"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
        :scroll="{ x: 1200 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'roles'">
            <a-space wrap>
               <a-tag v-for="role in record.roles" :key="role.id" color="blue">
                {{ role.name }}
              </a-tag>
            </a-space>
          </template>
          
          <template v-if="column.key === 'status'">
            <a-switch 
              :checked="record.is_active" 
              checked-children="开启" 
              un-checked-children="禁用"
              :disabled="true" 
            />
          </template>
          
          <!-- 预留字段展示 -->
          <template v-if="column.dataIndex === 'realName'">
             <span class="text-gray-400">-</span>
          </template>
           <template v-if="column.dataIndex === 'mobile'">
             <span class="text-gray-400">-</span>
          </template>
           <template v-if="column.key === 'last_login'">
             <div class="text-xs text-gray-500">
               <div>2025-11-22 10:00</div>
               <div>192.168.1.1</div>
             </div>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
              <a-dropdown>
                 <a class="ant-dropdown-link text-blue-500 text-sm" @click.prevent>
                   更多
                 </a>
                 <template #overlay>
                   <a-menu>
                     <a-menu-item @click="handleResetPwd(record)">重置密码</a-menu-item>
                     <a-menu-item danger @click="handleDelete(record)">删除用户</a-menu-item>
                   </a-menu>
                 </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- Modals (保持不变或微调) -->
    <a-modal
      v-model:open="modalVisible"
      :title="modalType === 'create' ? '新增用户' : '编辑用户'"
      @ok="handleSubmit"
    >
      <a-form :model="formData" layout="vertical">
        <a-form-item label="用户名" required>
          <a-input v-model:value="formData.username" />
        </a-form-item>
        <a-form-item label="邮箱" required>
          <a-input v-model:value="formData.email" />
        </a-form-item>
        <a-form-item label="密码" :required="modalType === 'create'" v-if="modalType === 'create'">
          <a-input-password v-model:value="formData.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item label="角色">
          <a-select v-model:value="formData.role_ids" mode="multiple" placeholder="选择角色">
            <a-select-option v-for="role in roles" :key="role.id" :value="role.id">
              {{ role.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="formData.is_active" />
          <span class="ml-2">{{ formData.is_active ? '激活' : '禁用' }}</span>
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="resetPwdVisible"
      title="重置密码"
      @ok="submitResetPwd"
      width="400px"
    >
      <p>正在重置用户 <b>{{ resetPwdData.username }}</b> 的密码。</p>
      <a-form layout="vertical">
        <a-form-item label="新密码" required>
          <a-input-password v-model:value="resetPwdData.password" placeholder="请输入新密码" />
        </a-form-item>
      </a-form>
    </a-modal>
  </Page>
</template>
