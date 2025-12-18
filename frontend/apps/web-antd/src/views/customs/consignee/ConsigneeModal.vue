<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Modal, Form, Input, Checkbox, message, Select } from 'ant-design-vue';
import { createOverseasConsignee, updateOverseasConsignee, type OverseasConsignee } from '#/api/customs/consignee';
import { getDictItemsApi, type DictItem } from '#/api/system/dict';

const props = defineProps<{
  open: boolean;
  record: OverseasConsignee | null;
}>();

const emit = defineEmits(['update:open', 'success']);

const loading = ref(false);
const formRef = ref();
const countryOptions = ref<DictItem[]>([]);

const formState = ref<Partial<OverseasConsignee>>({
  name: '',
  address: '',
  contact_info: '',
  country: '',
  is_active: true
});

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
};

const isEdit = computed(() => !!props.record?.id);
const title = computed(() => isEdit.value ? '编辑收货人' : '新建收货人');

watch(
  () => props.open,
  (val) => {
    if (val) {
      if (props.record) {
        formState.value = { ...props.record };
      } else {
        formState.value = { is_active: true };
      }
      loadCountries();
    }
  }
);

async function loadCountries() {
    if (countryOptions.value.length > 0) return;
    try {
        countryOptions.value = await getDictItemsApi('country');
    } catch(e) { console.error(e); }
}

async function handleOk() {
  try {
    await formRef.value?.validate();
    loading.value = true;
    
    if (isEdit.value && props.record?.id) {
        await updateOverseasConsignee(props.record.id, formState.value);
        message.success('更新成功');
    } else {
        await createOverseasConsignee(formState.value);
        message.success('创建成功');
    }
    
    emit('success');
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function handleCancel() {
  emit('update:open', false);
}
</script>

<template>
  <Modal
    :open="open"
    :title="title"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <Form
      ref="formRef"
      :model="formState"
      :rules="rules"
      layout="vertical"
      class="pt-4"
    >
      <Form.Item label="名称" name="name">
        <Input v-model:value="formState.name" placeholder="请输入收货人名称" />
      </Form.Item>
      
      <Form.Item label="国家/地区" name="country">
        <Select 
            v-model:value="formState.country" 
            show-search
            :options="countryOptions"
            placeholder="请选择"
        />
      </Form.Item>

      <Form.Item label="联系方式" name="contact_info">
        <Input v-model:value="formState.contact_info" placeholder="电话/邮箱等" />
      </Form.Item>

      <Form.Item label="地址" name="address">
        <Input.TextArea v-model:value="formState.address" :rows="3" placeholder="详细地址" />
      </Form.Item>

      <Form.Item name="is_active">
        <Checkbox v-model:checked="formState.is_active">启用</Checkbox>
      </Form.Item>
    </Form>
  </Modal>
</template>

