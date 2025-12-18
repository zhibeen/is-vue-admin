<script setup lang="ts">
import { useVbenModal } from '@vben/common-ui';
import { useVbenForm } from '#/adapter/form';
import { importDeclarationApi } from '#/api/customs/declaration';
import { message, Upload } from 'ant-design-vue';
import { InboxOutlined } from '@ant-design/icons-vue';
import { ref } from 'vue';

const emit = defineEmits(['success']);

const fileList = ref<any[]>([]);

const [Form, formApi] = useVbenForm({
  wrapperClass: 'grid-cols-12 gap-4',
  commonConfig: {
    labelWidth: 80,
  },
  schema: [
    {
      component: 'Input',
      fieldName: 'shipping_no',
      label: '提单号',
      formItemClass: 'col-span-6',
      componentProps: { placeholder: '请输入提单号/柜号' },
    },
    {
      component: 'Input',
      fieldName: 'logistics_provider',
      label: '物流商',
      formItemClass: 'col-span-6',
      componentProps: { placeholder: '请输入物流服务商' },
    },
    {
      component: 'Select',
      fieldName: 'container_mode',
      label: '货柜模式',
      formItemClass: 'col-span-6',
      defaultValue: 'FCL',
      componentProps: {
        options: [
            { label: '整柜 (FCL)', value: 'FCL' },
            { label: '散货 (LCL)', value: 'LCL' },
        ],
      },
    },
    {
      component: 'DatePicker',
      fieldName: 'export_date',
      label: '发货日期',
      rules: 'required',
      formItemClass: 'col-span-12',
      componentProps: { 
        valueFormat: 'YYYY-MM-DD',
        class: 'w-full',
        placeholder: '请选择发货/出口日期'
      },
    },
  ],
});

const [Modal, modalApi] = useVbenModal({
  title: '导入装箱单/报关草单',
  draggable: true,
  onConfirm: async () => {
    try {
      await formApi.validate();
      
      if (fileList.value.length === 0) {
        message.warning('请上传 Excel 文件');
        return;
      }
      
      const values = await formApi.getValues();
      const file = fileList.value[0].originFileObj;
      
      modalApi.setState({ loading: true, confirmLoading: true });
      
      await importDeclarationApi({
        file,
        shipping_no: values.shipping_no,
        logistics_provider: values.logistics_provider,
        container_mode: values.container_mode,
        export_date: values.export_date,
      });
      
      message.success('导入成功');
      emit('success');
      modalApi.close();
      fileList.value = [];
      formApi.resetValues();
      
    } catch (e) {
      console.error(e);
    } finally {
      modalApi.setState({ loading: false, confirmLoading: false });
    }
  },
});

const beforeUpload = (file: any) => {
  fileList.value = [...fileList.value, file];
  return false; // Prevent auto upload
};

const handleRemove = (file: any) => {
  const index = fileList.value.indexOf(file);
  const newFileList = fileList.value.slice();
  newFileList.splice(index, 1);
  fileList.value = newFileList;
};
</script>

<template>
  <Modal>
    <div class="p-4 flex flex-col gap-4">
      <Form />
      
      <div class="pl-4 pr-4">
          <div class="mb-2 text-sm text-gray-600">装箱单文件 (Excel):</div>
          <Upload.Dragger
            v-model:fileList="fileList"
            name="file"
            :maxCount="1"
            :before-upload="beforeUpload"
            @remove="handleRemove"
            accept=".xlsx,.xls"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持 .xlsx, .xls 格式。请确保包含 SKU, Quantity, Supplier 等列。
            </p>
          </Upload.Dragger>
      </div>
    </div>
  </Modal>
</template>

