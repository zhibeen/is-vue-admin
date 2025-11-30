<script setup lang="ts">
import { ref, computed } from 'vue';
import { useVbenDrawer } from '@vben/common-ui';
import { useVbenForm } from '#/adapter/form';
import { createCompany, updateCompany } from '#/api/serc/foundation';
import { message } from 'ant-design-vue';

const emit = defineEmits(['success']);

const isUpdate = ref(false);
const recordId = ref<number | null>(null);

const getTitle = computed(() => (isUpdate.value ? '编辑采购主体' : '新增采购主体'));

const [Form, formApi] = useVbenForm({
  wrapperClass: 'grid-cols-1',
  schema: [
    {
      component: 'Input',
      fieldName: 'name',
      label: '公司名称',
      rules: 'required',
    },
    {
      component: 'Input',
      fieldName: 'tax_id',
      label: '纳税人识别号',
    },
    {
      component: 'InputTextArea',
      fieldName: 'address',
      label: '注册地址',
    },
    {
      component: 'InputTextArea',
      fieldName: 'bank_info_json',
      label: '银行账户 (JSON)',
      defaultValue: '{}',
      help: '{"bank": "ICBC", "account": "123456"}',
    },
  ],
});

const [Drawer, drawerApi] = useVbenDrawer({
  onConfirm: async () => {
    try {
      const values = await formApi.validate();
      
      // Parse JSON
      let bankInfo = {};
      try {
        if (values.bank_info_json) {
          bankInfo = JSON.parse(values.bank_info_json);
        }
      } catch {
        // ignore
      }

      const payload = {
        ...values,
        bank_info: bankInfo,
      };
      delete payload.bank_info_json;

      if (isUpdate.value && recordId.value) {
        await updateCompany(recordId.value, payload);
        message.success('更新成功');
      } else {
        await createCompany(payload);
        message.success('创建成功');
      }
      
      emit('success');
      drawerApi.close();
    } catch (error) {
      console.error(error);
    }
  },
  onOpenChange: (isOpen) => {
    if (isOpen) {
      const { record, isUpdate: isUp } = drawerApi.getData() || {};
      isUpdate.value = !!isUp;
      recordId.value = record?.id || null;
      
      if (isUp && record) {
        formApi.setValues({
          ...record,
          bank_info_json: JSON.stringify(record.bank_info || {}, null, 2),
        });
      } else {
        formApi.resetValues();
      }
    }
  },
});
</script>

<template>
  <Drawer :title="getTitle">
    <Form />
  </Drawer>
</template>

