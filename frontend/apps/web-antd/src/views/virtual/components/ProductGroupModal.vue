<template>
  <a-modal
    v-model:visible="visible"
    :title="mode === 'create' ? '新建SKU分组' : '编辑SKU分组'"
    width="500px"
    :confirm-loading="confirmLoading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-form
      ref="formRef"
      :model="formState"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 16 }"
      :rules="rules"
    >
      <a-form-item label="分组编码" name="code">
        <a-input
          v-model:value="formState.code"
          placeholder="请输入分组编码"
          :disabled="mode === 'edit'"
        />
        <div class="text-gray-500 text-xs mt-1">
          编码唯一，用于系统识别
        </div>
      </a-form-item>

      <a-form-item label="分组名称" name="name">
        <a-input
          v-model:value="formState.name"
          placeholder="请输入分组名称"
        />
        <div class="text-gray-500 text-xs mt-1">
          例如：黑五大促组、清仓处理组、新品推广组
        </div>
      </a-form-item>

      <a-form-item label="备注" name="note">
        <a-textarea
          v-model:value="formState.note"
          placeholder="请输入分组备注说明"
          :rows="3"
        />
        <div class="text-gray-500 text-xs mt-1">
          描述分组用途和范围
        </div>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue';
import type { FormInstance } from 'ant-design-vue';
import { message } from 'ant-design-vue';
import type { ProductGroup, ProductGroupForm } from '#/api/virtual';

interface Props {
  visible: boolean;
  record?: ProductGroup | null;
  mode: 'create' | 'edit';
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  record: null,
  mode: 'create'
});

const emit = defineEmits<Emits>();

const formRef = ref<FormInstance>();
const confirmLoading = ref(false);

// 表单状态
const formState = reactive<ProductGroupForm>({
  code: '',
  name: '',
  note: ''
});

// 表单验证规则
const rules = {
  code: [
    { required: true, message: '请输入分组编码', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '编码只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入分组名称', trigger: 'blur' }
  ]
};

// 监听 visible 变化
watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => {
      if (props.record && props.mode === 'edit') {
        // 编辑模式，填充数据
        Object.assign(formState, {
          code: props.record.code,
          name: props.record.name,
          note: props.record.note || ''
        });
      } else {
        // 创建模式，重置表单
        formRef.value?.resetFields();
        Object.assign(formState, {
          code: '',
          name: '',
          note: ''
        });
      }
    });
  }
});

// 确定
const handleOk = async () => {
  try {
    await formRef.value?.validate();
    confirmLoading.value = true;

    // TODO: 调用创建/更新 API
    if (props.mode === 'create') {
      // await createProductGroup(formState);
      message.success('创建成功');
    } else {
      // await updateProductGroup(props.record!.id, formState);
      message.success('更新成功');
    }

    emit('success');
    handleCancel();
  } catch (error) {
    console.error('表单验证失败:', error);
  } finally {
    confirmLoading.value = false;
  }
};

// 取消
const handleCancel = () => {
  emit('update:visible', false);
};
</script>
