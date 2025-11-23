<script lang="ts" setup>
import { ref, reactive } from 'vue';
import { Modal, Form, FormItem, Input, message } from 'ant-design-vue';
import { createRoleApi, updateRoleApi, type RoleItem } from '#/api/core/system';

const emit = defineEmits<{
  (e: 'success'): void;
}>();

const visible = ref(false);
const modalType = ref<'create' | 'edit'>('create');
const formData = reactive({
  id: 0,
  name: '',
  description: '',
  permission_ids: [] as number[],
});

const open = (type: 'create' | 'edit', role?: RoleItem) => {
  modalType.value = type;
  if (type === 'create') {
    Object.assign(formData, { 
      id: 0, 
      name: role ? `${role.name}_copy` : '', // Handle copy case
      description: role ? role.description : '', 
      permission_ids: role ? role.permissions.map(p => p.id) : [] 
    });
  } else if (role) {
    Object.assign(formData, {
      id: role.id,
      name: role.name,
      description: role.description,
      permission_ids: role.permissions.map(p => p.id)
    });
  }
  visible.value = true;
};

const handleSubmit = async () => {
  try {
    if (!formData.name) {
      message.error('请输入角色名称');
      return;
    }
    const payload = {
      name: formData.name,
      description: formData.description,
      permission_ids: formData.permission_ids
    };

    if (modalType.value === 'create') {
      await createRoleApi(payload);
      message.success('创建成功');
    } else {
      await updateRoleApi(formData.id, payload);
      message.success('更新成功');
    }
    visible.value = false;
    emit('success');
  } catch (error) {
    console.error(error);
  }
};

defineExpose({ open });
</script>

<template>
  <Modal 
    v-model:open="visible" 
    :title="modalType === 'create' ? '新增角色' : '编辑角色'" 
    @ok="handleSubmit"
  >
    <Form layout="vertical">
      <FormItem label="角色名称" required>
        <Input v-model:value="formData.name" placeholder="例如: product_manager" />
      </FormItem>
      <FormItem label="描述">
        <Input.TextArea v-model:value="formData.description" placeholder="该角色的职责描述" />
      </FormItem>
    </Form>
  </Modal>
</template>

