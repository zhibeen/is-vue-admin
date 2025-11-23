<script lang="ts" setup>
import { ref, watch, computed, onMounted } from 'vue';
import { 
  Alert,
  Popover,
  Input,
  Checkbox,
  CheckboxGroup,
  Button,
  Table,
  Tooltip,
  Radio,
  type TableColumnsType
} from 'ant-design-vue';
import { 
  SearchOutlined, 
  DownOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue';
import { 
  getDataPermissionMetasApi,
  getRoleDataPermissionApi,
  saveRoleDataPermissionsBulkApi,
  getUsersApi,
  type RoleItem,
  type DataPermMeta,
  type RoleDataPermConfig,
  type UserItem
} from '#/api/core/system';
import { message } from 'ant-design-vue';

const props = defineProps<{
  role: RoleItem;
}>();

const emit = defineEmits<{
  (e: 'dirty', val: boolean): void;
}>();

// State
const dataPermMetas = ref<DataPermMeta[]>([]);
const roleDataConfigs = ref<Record<string, RoleDataPermConfig>>({});
const allUsers = ref<UserItem[]>([]);
const globalTargetUserIds = ref<number[]>([]);
const isDataPermDirty = ref(false);

// User Selector State
const userSelectorVisible = ref(false);
const userSelectorSearchText = ref('');
const tempSelectedUserIds = ref<number[]>([]);

// Computed Table Data
const flatDataPermTableData = computed(() => {
  const list: any[] = [];
  dataPermMetas.value.forEach(cat => {
    let catRowSpan = 0;
    if (cat.children) {
      cat.children.forEach(mod => {
        if (mod.children) catRowSpan += mod.children.length;
      });
    }
    if (catRowSpan === 0) return; 

    let isFirstInCat = true;
    if (cat.children) {
      cat.children.forEach(mod => {
        if (mod.children && mod.children.length > 0) {
          mod.children.forEach((res, resIndex) => {
             list.push({
               key: res.key,
               categoryKey: cat.key,
               categoryName: cat.label,
               categoryDesc: cat.description,
               categoryRowSpan: isFirstInCat ? catRowSpan : 0,
               moduleName: mod.label,
               moduleRowSpan: resIndex === 0 ? mod.children.length : 0,
               resourceName: res.label,
               resourceKey: res.key
             });
             isFirstInCat = false;
          });
        }
      });
    }
  });
  return list;
});

const columns: TableColumnsType = [
  { 
    title: '权限大类', 
    dataIndex: 'categoryName', 
    key: 'category',
    width: 200,
    customCell: (record) => ({ rowSpan: record.categoryRowSpan }),
    fixed: 'left'
  },
  { 
    title: '模块', 
    dataIndex: 'moduleName', 
    key: 'module',
    width: 150,
    customCell: (record) => ({ rowSpan: record.moduleRowSpan })
  },
  { title: '功能', dataIndex: 'resourceName', key: 'resource', width: 200 },
  { title: '全选', key: 'selectAllAll', width: 120, align: 'left' },
  { title: '全选', key: 'selectAllCustom', width: 150, align: 'left' },
];

// Init Logic
const initData = async () => {
  // 1. Fetch Metas if needed
  if (dataPermMetas.value.length === 0) {
    dataPermMetas.value = await getDataPermissionMetasApi();
  }
  // 2. Fetch Users if needed
  if (allUsers.value.length === 0) {
    const res = await getUsersApi({ page: 1, per_page: 0 });
    allUsers.value = res.items;
  }
  
  // 3. Fetch Configs
  await fetchAllRoleDataConfigs();
};

const fetchAllRoleDataConfigs = async () => {
  roleDataConfigs.value = {};
  globalTargetUserIds.value = [];
  
  const promises = dataPermMetas.value.map(async (meta) => {
    try {
      const res = await getRoleDataPermissionApi(props.role.id, meta.key);
      roleDataConfigs.value[meta.key] = res;
    } catch (e) {
      // Default fallback
      roleDataConfigs.value[meta.key] = {
         category_key: meta.key,
         target_user_ids: [],
         resource_scopes: {}
      };
    }
  });
  
  await Promise.all(promises);
  
  // Sync global users
  const configs = Object.values(roleDataConfigs.value);
  let foundUsers = false;
  for (const config of configs) {
     if (config.target_user_ids && config.target_user_ids.length > 0) {
        globalTargetUserIds.value = [...config.target_user_ids];
        foundUsers = true;
        break; 
     }
  }
  if (!foundUsers) globalTargetUserIds.value = [0]; // Default to Self
  
  isDataPermDirty.value = false;
  emit('dirty', false);
};

// Interaction Logic
const handleScopeChange = (catKey: string, resKey: string, val: string) => {
  const config = roleDataConfigs.value[catKey];
  if (config) {
     config.resource_scopes[resKey] = val as 'all' | 'custom';
     isDataPermDirty.value = true;
     emit('dirty', true);
  }
};

const handleBatchSetScope = (scope: 'all' | 'custom', checked: boolean) => {
  if (!checked) return; 
  for (const catKey in roleDataConfigs.value) {
      const config = roleDataConfigs.value[catKey];
      if (!config) continue;
      for (const row of flatDataPermTableData.value) {
          if (row.categoryKey === catKey) {
             config.resource_scopes[row.resourceKey] = scope;
          }
      }
  }
  isDataPermDirty.value = true;
  emit('dirty', true);
};

const areAllScopes = (scope: 'all' | 'custom') => {
   if (flatDataPermTableData.value.length === 0) return false;
   for (const row of flatDataPermTableData.value) {
       const config = roleDataConfigs.value[row.categoryKey];
       if (!config) return false;
       const currentScope = config.resource_scopes[row.resourceKey] || 'custom'; 
       if (currentScope !== scope) return false;
   }
   return true;
};

// User Selector Logic
const allUserOptions = computed(() => {
  const users = allUsers.value.map(u => ({
    label: u.nickname ? `${u.username}(${u.nickname})` : u.username,
    value: u.id
  }));
  return [{ label: '本人', value: 0 }, ...users];
});

const filteredUserOptions = computed(() => {
  if (!userSelectorSearchText.value) return allUserOptions.value;
  const lowerKey = userSelectorSearchText.value.toLowerCase();
  return allUserOptions.value.filter(u => u.label.toLowerCase().includes(lowerKey));
});

const displaySelectedUserText = computed(() => {
   if (globalTargetUserIds.value.length === 0) return '未选择';
   const labels = globalTargetUserIds.value.map(id => {
      const opt = allUserOptions.value.find(o => o.value === id);
      return opt ? opt.label : id;
   });
   if (labels.length <= 2) return labels.join(', ');
   return `${labels[0]} 等${labels.length}人`;
});

const handleUserSelectorOk = () => {
   globalTargetUserIds.value = [...tempSelectedUserIds.value];
   isDataPermDirty.value = true;
   emit('dirty', true);
   userSelectorVisible.value = false;
};

// Save Logic
const save = async () => {
  try {
    const configsToSave = Object.values(roleDataConfigs.value).map(config => {
       config.target_user_ids = globalTargetUserIds.value; 
       return config;
    });
    
    await saveRoleDataPermissionsBulkApi(props.role.id, configsToSave);
    
    message.success('数据权限保存成功');
    isDataPermDirty.value = false;
    emit('dirty', false);
    return true;
  } catch (e) {
    console.error(e);
    return false;
  }
};

defineExpose({ save });

watch(() => props.role.id, () => {
  initData();
}, { immediate: true });

</script>

<template>
  <div class="flex flex-col h-full py-4">
    <Alert v-if="isDataPermDirty" class="mb-4" message="检测到权限变更，请点击右上角保存按钮生效。" type="info" show-icon />

    <!-- Global User Selector -->
    <div class="px-4 py-3 bg-white dark:bg-transparent mb-4 border border-gray-100 dark:border-gray-800 rounded-md shadow-sm">
      <div class="flex items-center">
          <span class="mr-3 font-medium text-gray-700 dark:text-gray-300">权限人可见规则:</span>
          <span class="mr-3 text-gray-500 dark:text-gray-400 text-xs">若功能设为"权限人可见"，则可见以下用户的数据 (适用于所有分类):</span>
          
          <Popover v-model:open="userSelectorVisible" trigger="click" placement="bottomLeft" :overlayStyle="{ width: '300px' }">
              <template #content>
                <div class="w-full">
                    <Input v-model:value="userSelectorSearchText" placeholder="搜索内容" class="mb-2" allow-clear>
                        <template #prefix><SearchOutlined class="text-gray-400"/></template>
                    </Input>
                    <div class="h-[250px] overflow-y-auto custom-scrollbar">
                      <CheckboxGroup v-model:value="tempSelectedUserIds" class="w-full flex flex-col">
                          <div v-for="u in filteredUserOptions" :key="u.value" class="py-1.5 px-1 hover:bg-gray-50 dark:hover:bg-gray-700 rounded flex items-center">
                            <Checkbox :value="u.value" class="w-full">
                              <span class="ml-1">{{ u.label }}</span>
                            </Checkbox>
                          </div>
                      </CheckboxGroup>
                    </div>
                    <div class="flex justify-end items-center mt-3 pt-2 border-t dark:border-gray-700 space-x-2">
                        <Button size="small" @click="userSelectorVisible = false">取消</Button>
                        <Button size="small" type="primary" @click="handleUserSelectorOk">确定</Button>
                    </div>
                </div>
              </template>
              <div 
                class="flex items-center justify-between border border-gray-300 dark:border-gray-700 rounded px-3 py-1 cursor-pointer hover:border-primary transition-colors bg-white dark:bg-transparent"
                style="min-width: 120px; max-width: 400px;"
                @click="() => { tempSelectedUserIds = [...globalTargetUserIds]; userSelectorVisible = true; }"
              >
                <div class="flex items-center truncate">
                    <span class="text-gray-500 dark:text-gray-400 mr-2">用户</span>
                    <span class="font-medium text-gray-800 dark:text-gray-200 truncate">{{ displaySelectedUserText }}</span>
                </div>
                <DownOutlined class="text-xs text-gray-400 ml-2" />
              </div>
          </Popover>
      </div>
    </div>

    <!-- Permission Table -->
    <div class="flex-1 overflow-y-auto">
      <Table
        :columns="columns"
        :data-source="flatDataPermTableData"
        :pagination="false"
        size="middle"
        bordered
        row-key="resourceKey"
        :scroll="{ y: 'calc(100vh - 420px)' }"
      >
        <template #headerCell="{ column }">
          <template v-if="column.key === 'selectAllAll'">
            <div class="flex items-center space-x-1">
              <Checkbox 
                :checked="areAllScopes('all')" 
                @change="(e) => handleBatchSetScope('all', e.target.checked)"
              />
              <span>全选</span>
            </div>
          </template>
          <template v-if="column.key === 'selectAllCustom'">
            <div class="flex items-center space-x-1">
              <Checkbox 
                :checked="areAllScopes('custom')" 
                @change="(e) => handleBatchSetScope('custom', e.target.checked)"
              />
              <span>全选</span>
            </div>
          </template>
        </template>

        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'category'">
            <div class="flex flex-col space-y-1">
              <div class="flex items-center">
                  <span class="font-bold text-base">{{ record.categoryName }}</span>
                  <Tooltip v-if="record.categoryDesc" :title="record.categoryDesc">
                    <InfoCircleOutlined class="ml-2 text-gray-400 cursor-help" />
                  </Tooltip>
              </div>
            </div>
          </template>

          <template v-if="column.key === 'selectAllAll'">
            <div v-if="roleDataConfigs[record.categoryKey]">
                <Radio 
                  :checked="roleDataConfigs[record.categoryKey]!.resource_scopes[record.resourceKey] === 'all'"
                  @click="handleScopeChange(record.categoryKey, record.resourceKey, 'all')"
                >
                  全部可见
                </Radio>
            </div>
          </template>
          
          <template v-if="column.key === 'selectAllCustom'">
            <div v-if="roleDataConfigs[record.categoryKey]">
                <Radio 
                  :checked="roleDataConfigs[record.categoryKey]!.resource_scopes[record.resourceKey] === 'custom' || !roleDataConfigs[record.categoryKey]!.resource_scopes[record.resourceKey]"
                  @click="handleScopeChange(record.categoryKey, record.resourceKey, 'custom')"
                >
                  权限人可见
                </Radio>
            </div>
          </template>
        </template>
      </Table>
    </div>
  </div>
</template>

