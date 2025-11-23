<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue';
import { 
  Alert,
  Table,
  Tooltip,
  Radio,
  message,
  type TableColumnsType
} from 'ant-design-vue';
import { InfoCircleOutlined } from '@ant-design/icons-vue';
import { 
  getFieldPermissionMetasApi,
  getRoleFieldPermissionsApi,
  saveRoleFieldPermissionsApi,
  type RoleItem,
  type FieldPermMeta,
  type RoleFieldPermConfig
} from '#/api/core/system';

const props = defineProps<{
  role: RoleItem;
}>();

const emit = defineEmits<{
  (e: 'dirty', val: boolean): void;
}>();

const fieldPermMetas = ref<FieldPermMeta[]>([]);
const roleFieldConfigs = ref<RoleFieldPermConfig[]>([]);
const isFieldPermDirty = ref(false);

const columns: TableColumnsType = [
  { title: '字段', dataIndex: 'label', key: 'label', width: 200 },
  { title: '可见', key: 'visible', align: 'center' },
  { title: '不可见', key: 'hidden', align: 'center' },
  { title: '仅跟进人可见', key: 'follower', align: 'center' },
];

const initData = async () => {
  try {
    if (fieldPermMetas.value.length === 0) {
        fieldPermMetas.value = await getFieldPermissionMetasApi();
    }
    roleFieldConfigs.value = await getRoleFieldPermissionsApi(props.role.id);
    isFieldPermDirty.value = false;
    emit('dirty', false);
  } catch (e) {
    console.error(e);
  }
};

const getFieldPermissionType = (fieldKey: string) => {
  const config = roleFieldConfigs.value.find(c => c.field_key === fieldKey);
  if (!config) return 'visible';
  
  if (!config.is_visible) return 'hidden';
  if (config.condition === 'follower') return 'follower';
  return 'visible';
};

const handleFieldPermissionChange = (fieldKey: string, type: 'visible' | 'hidden' | 'follower') => {
  const config = roleFieldConfigs.value.find(c => c.field_key === fieldKey);
  
  let is_visible = true;
  let condition = 'none';
  
  if (type === 'hidden') {
    is_visible = false;
  } else if (type === 'follower') {
    is_visible = true;
    condition = 'follower';
  }
  
  if (config) {
    config.is_visible = is_visible;
    config.condition = condition;
  } else {
    roleFieldConfigs.value.push({ field_key: fieldKey, is_visible, condition });
  }
  isFieldPermDirty.value = true;
  emit('dirty', true);
};

const save = async () => {
  try {
    await saveRoleFieldPermissionsApi(props.role.id, roleFieldConfigs.value);
    message.success('字段权限保存成功');
    isFieldPermDirty.value = false;
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
    <Alert v-if="isFieldPermDirty" class="mb-4" message="检测到字段权限变更，请点击右上角保存按钮生效。" type="info" show-icon />
    
    <div class="flex-1 overflow-y-auto">
      <Table
        :columns="columns"
        :data-source="fieldPermMetas"
        :pagination="false"
        size="middle"
        bordered
        row-key="field_key"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'label'">
            <div class="flex items-center">
              <span>{{ record.label }}</span>
              <Tooltip v-if="record.description" :title="record.description">
                <InfoCircleOutlined class="ml-2 text-gray-400 cursor-help" />
              </Tooltip>
            </div>
          </template>
          
          <template v-if="column.key === 'visible'">
            <Radio 
              :checked="getFieldPermissionType(record.field_key) === 'visible'"
              @click="handleFieldPermissionChange(record.field_key, 'visible')"
            />
          </template>
          
          <template v-if="column.key === 'hidden'">
            <Radio 
              :checked="getFieldPermissionType(record.field_key) === 'hidden'"
              @click="handleFieldPermissionChange(record.field_key, 'hidden')"
            />
          </template>
          
          <template v-if="column.key === 'follower'">
            <Radio 
              :checked="getFieldPermissionType(record.field_key) === 'follower'"
              @click="handleFieldPermissionChange(record.field_key, 'follower')"
            />
          </template>
        </template>
      </Table>
    </div>
  </div>
</template>

