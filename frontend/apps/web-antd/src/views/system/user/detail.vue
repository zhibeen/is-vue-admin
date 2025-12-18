<script lang="ts" setup>
import { ref, onMounted, reactive, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { 
  message, 
  Card, 
  Descriptions, 
  DescriptionsItem,
  Form, 
  FormItem, 
  Input, 
  InputPassword,
  Button, 
  Space, 
  Tag, 
  Switch, 
  Tabs,
  TabPane,
  Table,
  Checkbox,
  CheckboxGroup,
  Empty,
  Spin
} from 'ant-design-vue';
import { Page } from '@vben/common-ui';
import {
  getUsersApi, updateUserApi, getRolesApi, getPermissionsApi,
  type UserItem, type RoleItem, type PermissionItem
} from '#/api/core/system';
import { ArrowLeftOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue';

const route = useRoute();
const router = useRouter();

// State
const loading = ref(false);
const saving = ref(false);
const editMode = ref(false);
const userId = computed(() => Number(route.params.id));
const user = ref<UserItem | null>(null);
const roles = ref<RoleItem[]>([]);
const allPermissions = ref<PermissionItem[]>([]);

// 表单数据
const formData = reactive({
  realname: '',
  nickname: '',
  mobile: '',
  email: '',
  is_active: true,
  role_ids: [] as number[],
  changePassword: false,
  password: ''
});

// 加载用户数据
const loadUser = async () => {
  loading.value = true;
  try {
    const res = await getUsersApi({ page: 1, per_page: 999 });
    user.value = res.items.find(u => u.id === userId.value) || null;
    
    if (user.value) {
      Object.assign(formData, {
        realname: user.value.realname || '',
        nickname: user.value.nickname || '',
        mobile: user.value.mobile || '',
        email: user.value.email,
        is_active: user.value.is_active,
        role_ids: user.value.roles.map(r => r.id),
        changePassword: false,
        password: ''
      });
    }
  } catch (error) {
    console.error('加载用户失败:', error);
    message.error('加载用户信息失败');
  } finally {
    loading.value = false;
  }
};

// 加载角色列表
const loadRoles = async () => {
  try {
    roles.value = await getRolesApi();
  } catch (error) {
    console.error('加载角色失败:', error);
  }
};

// 加载权限列表
const loadPermissions = async () => {
  try {
    allPermissions.value = await getPermissionsApi();
  } catch (error) {
    console.error('加载权限失败:', error);
  }
};

// 计算用户继承的权限
const inheritedPermissions = computed(() => {
  if (!user.value) return [];
  const permSet = new Set<string>();
  user.value.roles.forEach(role => {
    role.permissions?.forEach((perm: any) => {
      permSet.add(perm.name);
    });
  });
  return Array.from(permSet);
});

// 权限分组（按模块）
const permissionsByModule = computed(() => {
  const groups: Record<string, PermissionItem[]> = {};
  allPermissions.value.forEach(perm => {
    const module = perm.module || '其他';
    if (!groups[module]) {
      groups[module] = [];
    }
    groups[module].push(perm);
  });
  return groups;
});

// 保存修改
const handleSave = async () => {
  if (!user.value) return;
  
  // 验证
  if (!formData.email) {
    message.error('请输入邮箱');
    return;
  }
  
  if (formData.changePassword && !formData.password) {
    message.error('请输入新密码');
    return;
  }
  
  if (formData.changePassword && formData.password.length < 6) {
    message.error('密码至少6位');
    return;
  }
  
  saving.value = true;
  try {
    const payload: any = {
      realname: formData.realname || undefined,
      nickname: formData.nickname || undefined,
      mobile: formData.mobile || undefined,
      email: formData.email,
      is_active: formData.is_active,
      role_ids: formData.role_ids
    };
    
    if (formData.changePassword && formData.password) {
      payload.password = formData.password;
    }
    
    await updateUserApi(user.value.id, payload);
    message.success('保存成功');
    editMode.value = false;
    formData.changePassword = false;
    formData.password = '';
    await loadUser();
  } catch (error: any) {
    console.error('保存失败:', error);
    message.error(error.message || '保存失败');
  } finally {
    saving.value = false;
  }
};

// 取消编辑
const handleCancel = () => {
  editMode.value = false;
  if (user.value) {
    Object.assign(formData, {
      realname: user.value.realname || '',
      nickname: user.value.nickname || '',
      mobile: user.value.mobile || '',
      email: user.value.email,
      is_active: user.value.is_active,
      role_ids: user.value.roles.map(r => r.id),
      changePassword: false,
      password: ''
    });
  }
};

// 返回列表
const handleBack = () => {
  router.push('/system/user');
};

onMounted(() => {
  loadUser();
  loadRoles();
  loadPermissions();
});
</script>

<template>
  <Page title="用户详情" :loading="loading">
    <!-- 顶部操作栏 -->
    <div class="mb-4 flex items-center justify-between">
      <Button @click="handleBack">
        <template #icon><ArrowLeftOutlined /></template>
        返回列表
      </Button>
      
      <Space v-if="!editMode">
        <Button type="primary" @click="editMode = true">
          <template #icon><EditOutlined /></template>
          编辑
        </Button>
      </Space>
      
      <Space v-else>
        <Button @click="handleCancel">取消</Button>
        <Button type="primary" :loading="saving" @click="handleSave">
          <template #icon><SaveOutlined /></template>
          保存
        </Button>
      </Space>
    </div>

    <Spin :spinning="loading">
      <div v-if="user" class="grid grid-cols-12 gap-4">
        <!-- 左侧：基本信息 -->
        <div class="col-span-4">
          <Card title="基本信息" :bordered="false">
            <template v-if="!editMode">
              <Descriptions :column="1" bordered size="small">
                <DescriptionsItem label="用户名">{{ user.username }}</DescriptionsItem>
                <DescriptionsItem label="姓名">{{ user.realname || '-' }}</DescriptionsItem>
                <DescriptionsItem label="昵称">{{ user.nickname || '-' }}</DescriptionsItem>
                <DescriptionsItem label="手机号">{{ user.mobile || '-' }}</DescriptionsItem>
                <DescriptionsItem label="邮箱">{{ user.email }}</DescriptionsItem>
                <DescriptionsItem label="状态">
                  <Tag :color="user.is_active ? 'green' : 'red'">
                    {{ user.is_active ? '激活' : '禁用' }}
                  </Tag>
                </DescriptionsItem>
                <DescriptionsItem label="创建时间">{{ user.created_at }}</DescriptionsItem>
              </Descriptions>
            </template>
            
            <template v-else>
              <Form layout="vertical" :model="formData">
                <FormItem label="用户名">
                  <Input :value="user.username" disabled />
                  <div class="text-xs text-gray-500 mt-1">用户名不可修改</div>
                </FormItem>
                
                <FormItem label="姓名">
                  <Input v-model:value="formData.realname" placeholder="请输入真实姓名" />
                </FormItem>
                
                <FormItem label="昵称">
                  <Input v-model:value="formData.nickname" placeholder="请输入昵称" />
                </FormItem>
                
                <FormItem label="手机号">
                  <Input v-model:value="formData.mobile" placeholder="请输入手机号" :maxlength="11" />
                </FormItem>
                
                <FormItem label="邮箱" required>
                  <Input v-model:value="formData.email" placeholder="请输入邮箱" type="email" />
                </FormItem>
                
                <FormItem label="状态">
                  <Switch v-model:checked="formData.is_active" />
                  <span class="ml-2">{{ formData.is_active ? '激活' : '禁用' }}</span>
                </FormItem>
                
                <FormItem>
                  <Checkbox v-model:checked="formData.changePassword">
                    修改密码
                  </Checkbox>
                </FormItem>
                
                <FormItem v-if="formData.changePassword" label="新密码" required>
                  <InputPassword v-model:value="formData.password" placeholder="请输入新密码（至少6位）" />
                </FormItem>
              </Form>
            </template>
          </Card>
        </div>

        <!-- 右侧：标签页 -->
        <div class="col-span-8">
          <Card :bordered="false">
            <Tabs>
              <!-- 角色标签页 -->
              <TabPane key="roles" tab="角色">
                <div class="mb-4">
                  <div class="text-sm text-gray-600 mb-2">当前角色：</div>
                  <Space wrap v-if="!editMode">
                    <Tag v-for="role in user.roles" :key="role.id" color="blue" class="text-base px-3 py-1">
                      {{ role.name }}
                    </Tag>
                    <span v-if="user.roles.length === 0" class="text-gray-400">未分配角色</span>
                  </Space>
                  
                  <CheckboxGroup v-else v-model:value="formData.role_ids" class="w-full">
                    <div class="grid grid-cols-2 gap-3">
                      <Card 
                        v-for="role in roles" 
                        :key="role.id" 
                        size="small"
                        :class="{'border-blue-500': formData.role_ids.includes(role.id)}"
                      >
                        <Checkbox :value="role.id">
                          <div>
                            <div class="font-medium">{{ role.name }}</div>
                            <div class="text-xs text-gray-500">{{ role.description }}</div>
                          </div>
                        </Checkbox>
                      </Card>
                    </div>
                  </CheckboxGroup>
                </div>
                
                <div v-if="user.roles.length > 0" class="mt-6 pt-4 border-t">
                  <div class="text-sm text-gray-600 mb-2">继承的权限数量：</div>
                  <div class="text-2xl font-bold text-blue-600">{{ inheritedPermissions.length }}</div>
                  <div class="text-xs text-gray-500 mt-1">该用户通过角色继承了以上数量的权限</div>
                </div>
              </TabPane>

              <!-- 功能权限标签页 -->
              <TabPane key="permissions" tab="功能权限">
                <div v-if="inheritedPermissions.length > 0">
                  <div class="mb-3 text-sm text-gray-600">
                    该用户通过角色继承的所有功能权限（只读）：
                  </div>
                  
                  <div v-for="(perms, module) in permissionsByModule" :key="module" class="mb-4">
                    <div class="font-medium mb-2 text-gray-700">{{ module }}</div>
                    <Space wrap>
                      <Tag 
                        v-for="perm in perms.filter(p => inheritedPermissions.includes(p.name))" 
                        :key="perm.id"
                        :color="inheritedPermissions.includes(perm.name) ? 'green' : 'default'"
                      >
                        {{ perm.description || perm.name }}
                      </Tag>
                    </Space>
                  </div>
                </div>
                <Empty v-else description="该用户未分配任何角色，没有权限" />
              </TabPane>

              <!-- 数据权限标签页 -->
              <TabPane key="data-permission" tab="数据权限">
                <Empty description="数据权限配置功能开发中" />
              </TabPane>

              <!-- 操作日志标签页 -->
              <TabPane key="logs" tab="操作日志">
                <Empty description="操作日志功能开发中" />
              </TabPane>
            </Tabs>
          </Card>
        </div>
      </div>
      
      <Empty v-else description="用户不存在" />
    </Spin>
  </Page>
</template>

<style scoped>
:deep(.ant-descriptions-item-label) {
  width: 100px;
  font-weight: 500;
}
</style>

