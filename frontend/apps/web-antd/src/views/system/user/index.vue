<script lang="ts" setup>
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { 
  message, 
  Modal, 
  Form, 
  FormItem, 
  Select, 
  SelectOption,
  Input, 
  InputPassword,
  Button, 
  Space, 
  Table, 
  Tag, 
  Switch, 
  Dropdown, 
  Menu, 
  MenuItem,
  Checkbox 
} from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import {
  getUsersApi, createUserApi, updateUserApi, deleteUserApi, getRolesApi,
  type UserItem, type RoleItem
} from '#/api/core/system';
import { 
  PlusOutlined, DeleteOutlined, ReloadOutlined, 
  SearchOutlined, ExportOutlined 
} from '@ant-design/icons-vue';

const router = useRouter();

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
  realname: '',
  nickname: '',
  mobile: '',
  password: '',
  role_ids: [] as number[],
  is_active: true,
  changePassword: false,
});

// Reset Password State
const resetPwdVisible = ref(false);
const resetPwdData = reactive({ id: 0, password: '', username: '' });

// 列定义
const columns: any[] = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '用户名', dataIndex: 'username', width: 120 },
  { title: '姓名', dataIndex: 'realname', width: 100 },
  { title: '昵称', dataIndex: 'nickname', width: 100 },
  { title: '手机号', dataIndex: 'mobile', width: 130 },
  { title: '邮箱', dataIndex: 'email', width: 200 },
  { title: '角色', key: 'roles', width: 180 },
  { title: '状态', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', key: 'action', fixed: 'right' as const, width: 200 },
];

// Actions
const fetchRoles = async () => {
  try {
    roles.value = await getRolesApi();
  } catch (error) {
    console.error('获取角色列表失败:', error);
  }
};

const fetchUsers = async () => {
  loading.value = true;
  try {
    const res = await getUsersApi({
      page: pagination.current,
      per_page: pagination.pageSize,
    });
    users.value = res.items;
    pagination.total = res.total;
  } catch (error) {
    console.error('获取用户列表失败:', error);
    message.error('获取用户列表失败');
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

const handleViewDetail = (record: UserItem) => {
  router.push(`/system/user/${record.id}`);
};

const handleAdd = () => {
  modalType.value = 'create';
  Object.assign(formData, {
    id: 0, 
    username: '', 
    email: '', 
    realname: '',
    nickname: '',
    mobile: '',
    password: '', 
    role_ids: [], 
    is_active: true,
    changePassword: false
  });
  modalVisible.value = true;
};

const handleEdit = (record: UserItem) => {
  modalType.value = 'edit';
  Object.assign(formData, {
    id: record.id,
    username: record.username,
    email: record.email,
    realname: record.realname || '',
    nickname: record.nickname || '',
    mobile: record.mobile || '',
    password: '',
    role_ids: record.roles.map(r => r.id),
    is_active: record.is_active,
    changePassword: false
  });
  modalVisible.value = true;
};

const handleDelete = (record: UserItem) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除用户 ${record.username} 吗？此操作不可恢复。`,
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      try {
        await deleteUserApi(record.id);
        message.success('删除成功');
        fetchUsers();
      } catch (error) {
        console.error('删除失败:', error);
        message.error('删除失败');
      }
    }
  });
};

const handleStatusChange = async (record: UserItem, checked: boolean) => {
  try {
    await updateUserApi(record.id, { is_active: checked });
    message.success('状态更新成功');
    fetchUsers();
  } catch (error) {
    console.error('状态更新失败:', error);
    message.error('状态更新失败');
  }
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
  } catch (error: any) {
    console.error('密码重置失败:', error);
    message.error(error.message || '密码重置失败');
  }
};

const handleSubmit = async () => {
  try {
    // 基础验证
    if (!formData.username || !formData.email) {
      message.error('请填写用户名和邮箱');
      return;
    }
    
    // 邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      message.error('请输入有效的邮箱地址');
      return;
    }
    
    // 手机号验证（如果填写了）
    if (formData.mobile) {
      const mobileRegex = /^1[3-9]\d{9}$/;
      if (!mobileRegex.test(formData.mobile)) {
        message.error('请输入有效的手机号');
        return;
      }
    }

    if (modalType.value === 'create' && !formData.password) {
      message.error('创建用户必须填写密码');
      return;
    }
    
    if (formData.password && formData.password.length < 6) {
      message.error('密码至少6位');
      return;
    }

    const payload: any = {
      username: formData.username,
      email: formData.email,
      realname: formData.realname || undefined,
      nickname: formData.nickname || undefined,
      mobile: formData.mobile || undefined,
      role_ids: formData.role_ids,
      is_active: formData.is_active,
    };

    // 创建时必须有密码，编辑时只在勾选修改密码时传递
    if (modalType.value === 'create') {
      payload.password = formData.password;
    } else if (formData.changePassword && formData.password) {
      payload.password = formData.password;
    }

    if (modalType.value === 'create') {
      await createUserApi(payload);
      message.success('创建成功');
    } else {
      await updateUserApi(formData.id, payload);
      message.success('更新成功');
    }
    
    modalVisible.value = false;
    fetchUsers();
  } catch (error: any) {
    console.error('操作失败:', error);
    message.error(error.message || '操作失败');
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
      <Form layout="inline" :model="searchForm">
        <FormItem label="用户状态">
          <Select v-model:value="searchForm.status" placeholder="请选择" style="width: 120px" allow-clear>
            <SelectOption :value="1">开启</SelectOption>
            <SelectOption :value="0">禁用</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="用户角色">
          <Select v-model:value="searchForm.role_id" placeholder="请选择角色" style="width: 150px" allow-clear>
            <SelectOption v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="搜索用户">
          <Input v-model:value="searchForm.keyword" placeholder="用户名/邮箱/姓名" allow-clear style="width: 200px" />
        </FormItem>
        <FormItem>
          <Space>
            <Button type="primary" @click="handleSearch">
              <template #icon><SearchOutlined /></template>
              查询
            </Button>
            <Button @click="handleResetSearch">
              <template #icon><ReloadOutlined /></template>
              重置
            </Button>
          </Space>
        </FormItem>
      </Form>
    </div>

    <!-- 表格区域 -->
    <div class="bg-white p-4 rounded shadow-sm">
      <div class="mb-4 flex justify-between">
        <Space>
          <Button type="primary" @click="handleAdd">
            <template #icon><PlusOutlined /></template>
            添加用户
          </Button>
          <Button danger :disabled="true">
             <template #icon><DeleteOutlined /></template>
             批量删除
          </Button>
        </Space>
        <Space>
          <Button>
             <template #icon><ExportOutlined /></template>
             导出数据
          </Button>
        </Space>
      </div>

      <Table
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
            <Space wrap>
               <Tag v-for="role in record.roles" :key="role.id" color="blue">
                {{ role.name }}
              </Tag>
            </Space>
          </template>
          
          <template v-if="column.key === 'status'">
            <Switch 
              :checked="record.is_active" 
              checked-children="开启" 
              un-checked-children="禁用"
              @change="(checked: any) => handleStatusChange(record as UserItem, !!checked)"
            />
          </template>
          
          <!-- 姓名 -->
          <template v-if="column.dataIndex === 'realname'">
             <span :class="record.realname ? '' : 'text-gray-400'">
               {{ record.realname || '-' }}
             </span>
          </template>
          
          <!-- 昵称 -->
          <template v-if="column.dataIndex === 'nickname'">
             <span :class="record.nickname ? '' : 'text-gray-400'">
               {{ record.nickname || '-' }}
             </span>
          </template>
          
          <!-- 手机号 -->
          <template v-if="column.dataIndex === 'mobile'">
             <span :class="record.mobile ? '' : 'text-gray-400'">
               {{ record.mobile || '-' }}
             </span>
          </template>

          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="handleViewDetail(record as UserItem)">详情</Button>
              <Button type="link" size="small" @click="handleEdit(record as UserItem)">编辑</Button>
              <Dropdown>
                 <a class="ant-dropdown-link text-blue-500 text-sm" @click.prevent>
                   更多
                 </a>
                 <template #overlay>
                   <Menu>
                     <MenuItem @click="handleResetPwd(record as UserItem)">重置密码</MenuItem>
                     <MenuItem danger @click="handleDelete(record as UserItem)">删除用户</MenuItem>
                   </Menu>
                 </template>
              </Dropdown>
            </Space>
          </template>
        </template>
      </Table>
    </div>

    <!-- 用户编辑弹窗 - 优化布局 -->
    <Modal
      v-model:open="modalVisible"
      :title="modalType === 'create' ? '新增用户' : '编辑用户'"
      :width="800"
      @ok="handleSubmit"
      okText="保存"
      cancelText="取消"
    >
      <Form :model="formData" layout="vertical">
        <!-- 两列布局 -->
        <div class="grid grid-cols-2 gap-4">
          <!-- 左列 -->
          <div>
            <FormItem label="用户名" required>
              <Input 
                v-model:value="formData.username" 
                placeholder="请输入用户名" 
                :disabled="modalType === 'edit'" 
              />
              <div v-if="modalType === 'edit'" class="text-xs text-gray-500 mt-1">
                用户名创建后不可修改
              </div>
            </FormItem>
            
            <FormItem label="姓名">
              <Input 
                v-model:value="formData.realname" 
                placeholder="请输入真实姓名（选填）" 
              />
            </FormItem>
            
            <FormItem label="昵称">
              <Input 
                v-model:value="formData.nickname" 
                placeholder="请输入昵称（选填）" 
              />
            </FormItem>
          </div>
          
          <!-- 右列 -->
          <div>
            <FormItem label="手机号">
              <Input 
                v-model:value="formData.mobile" 
                placeholder="请输入11位手机号（选填）" 
                :maxlength="11"
              />
            </FormItem>
            
            <FormItem label="邮箱" required>
              <Input 
                v-model:value="formData.email" 
                placeholder="请输入邮箱" 
                type="email"
              />
            </FormItem>
            
            <FormItem label="状态">
              <Switch v-model:checked="formData.is_active" />
              <span class="ml-2">{{ formData.is_active ? '激活' : '禁用' }}</span>
            </FormItem>
          </div>
        </div>
        
        <!-- 密码区域（单列） -->
        <div class="border-t pt-4 mt-2">
          <!-- 创建模式：必须填写密码 -->
          <FormItem 
            v-if="modalType === 'create'" 
            label="密码" 
            required
          >
            <InputPassword 
              v-model:value="formData.password" 
              placeholder="请输入密码（至少6位）" 
            />
          </FormItem>
          
          <!-- 编辑模式：可选修改密码 -->
          <template v-if="modalType === 'edit'">
            <FormItem>
              <Checkbox v-model:checked="formData.changePassword">
                修改密码
              </Checkbox>
            </FormItem>
            <FormItem 
              v-if="formData.changePassword" 
              label="新密码" 
              required
            >
              <InputPassword 
                v-model:value="formData.password" 
                placeholder="请输入新密码（至少6位）" 
              />
            </FormItem>
          </template>
        </div>
        
        <!-- 角色区域（单列，优化展示） -->
        <div class="border-t pt-4 mt-2">
          <FormItem label="分配角色">
            <Select 
              v-model:value="formData.role_ids" 
              mode="multiple" 
              placeholder="选择角色（支持多选）"
              :max-tag-count="3"
              show-search
              :filter-option="(input: string, option: any) => {
                return option.children[0].children.toLowerCase().includes(input.toLowerCase())
              }"
            >
              <SelectOption v-for="role in roles" :key="role.id" :value="role.id">
                <div class="flex items-center justify-between">
                  <span>{{ role.name }}</span>
                  <span class="text-xs text-gray-400 ml-2">{{ role.description }}</span>
                </div>
              </SelectOption>
            </Select>
            <div class="text-xs text-gray-500 mt-1">
              用户将继承所选角色的所有权限
            </div>
          </FormItem>
        </div>
      </Form>
    </Modal>

    <Modal
      v-model:open="resetPwdVisible"
      title="重置密码"
      @ok="submitResetPwd"
      :width="400"
    >
      <p>正在重置用户 <b>{{ resetPwdData.username }}</b> 的密码。</p>
      <Form layout="vertical">
        <FormItem label="新密码" required>
          <InputPassword v-model:value="resetPwdData.password" placeholder="请输入新密码" />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>

