<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue';
import { 
  Checkbox,
  CheckboxGroup,
  Alert
} from 'ant-design-vue';
import { 
  getPermissionTreeApi,
  updateRoleApi,
  type RoleItem, 
  type PermissionModule 
} from '#/api/core/system';
import { message } from 'ant-design-vue';

const props = defineProps<{
  role: RoleItem;
}>();

const emit = defineEmits<{
  (e: 'dirty', val: boolean): void;
}>();

const permissionTree = ref<PermissionModule[]>([]);
const currentRolePerms = ref<number[]>([]);
const isPermsDirty = ref(false);

// Fetch Tree
const fetchPermissions = async () => {
  try {
    permissionTree.value = await getPermissionTreeApi();
  } catch (e) {
    console.error(e);
  }
};

// Helper
const getModulePermissionIds = (module: PermissionModule): number[] => {
  let ids: number[] = [];
  module.children.forEach(group => {
    group.permissions.forEach(p => ids.push(p.id));
  });
  return ids;
};

const getModuleCheckState = (moduleName: string) => {
  const module = permissionTree.value.find(m => m.name === moduleName);
  if (!module) return { checked: false, indeterminate: false };
  
  const allIds = getModulePermissionIds(module);
  const selectedIds = allIds.filter(id => currentRolePerms.value.includes(id));
  
  const checked = selectedIds.length === allIds.length && allIds.length > 0;
  const indeterminate = selectedIds.length > 0 && !checked;
  return { checked, indeterminate };
};

const handleModuleCheck = (moduleName: string, e: Event) => {
  const checked = (e.target as HTMLInputElement).checked;
  const module = permissionTree.value.find(m => m.name === moduleName);
  if (!module) return;
  
  const allIds = getModulePermissionIds(module);
  if (checked) {
    const toAdd = allIds.filter(id => !currentRolePerms.value.includes(id));
    currentRolePerms.value.push(...toAdd);
  } else {
    currentRolePerms.value = currentRolePerms.value.filter(id => !allIds.includes(id));
  }
  isPermsDirty.value = true;
  emit('dirty', true);
};

const handleGroupCheckChange = () => {
  isPermsDirty.value = true;
  emit('dirty', true);
};

// Expose save method to parent
const save = async () => {
  try {
    await updateRoleApi(props.role.id, {
      name: props.role.name,
      permission_ids: currentRolePerms.value
    });
    message.success('权限保存成功');
    isPermsDirty.value = false;
    emit('dirty', false);
    return true;
  } catch (e) {
    console.error(e);
    return false;
  }
};

defineExpose({ save });

watch(() => props.role, (newRole) => {
  currentRolePerms.value = newRole.permissions.map(p => p.id);
  isPermsDirty.value = false;
  emit('dirty', false);
}, { immediate: true });

onMounted(() => {
  fetchPermissions();
});
</script>

<template>
  <div class="h-full overflow-y-auto pb-6 py-4 px-2">
    <Alert v-if="isPermsDirty" class="mb-4" message="检测到权限变更，请点击右上角保存按钮生效。" type="info" show-icon />

    <div v-for="module in permissionTree" :key="module.name" class="mb-8 border border-gray-100 dark:border-gray-800 rounded-lg overflow-hidden shadow-sm">
      <div class="bg-gray-50 dark:bg-gray-800/50 px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
        <div class="flex items-center">
          <Checkbox 
              :checked="getModuleCheckState(module.name).checked"
              :indeterminate="getModuleCheckState(module.name).indeterminate"
              @change="(e: any) => handleModuleCheck(module.name, e)"
            >
              <span class="font-bold text-base">{{ module.label }}</span>
            </Checkbox>
        </div>
      </div>

      <div class="p-4 space-y-4 bg-white dark:bg-transparent">
        <div v-for="group in module.children" :key="group.name" class="flex flex-row items-start border-b border-gray-50 dark:border-gray-800 pb-4 last:border-0 last:pb-0">
          <div class="w-32 pt-1 font-medium text-gray-600 dark:text-gray-400">
            {{ group.label }}
          </div>
          
          <div class="flex-1">
            <CheckboxGroup v-model:value="currentRolePerms" @change="handleGroupCheckChange" class="w-full">
              <div class="flex flex-wrap gap-4">
                <Checkbox v-for="perm in group.permissions" :key="perm.id" :value="perm.id">
                  <span :title="perm.code">{{ perm.label }}</span>
                </Checkbox>
              </div>
            </CheckboxGroup>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="permissionTree.length === 0" class="text-center text-gray-400 py-10">
      加载权限配置中...
    </div>
  </div>
</template>

