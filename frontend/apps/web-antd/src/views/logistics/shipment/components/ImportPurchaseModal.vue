<script setup lang="ts">
/**
 * 批量导入采购明细Modal
 */
import { Modal, Alert, Button, Upload, message } from 'ant-design-vue';
import { UploadOutlined } from '@ant-design/icons-vue';
import { ref, watch } from 'vue';

interface Props {
  visible: boolean;
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const loading = ref(false);
const fileList = ref<any[]>([]);

// 处理文件上传
function handleChange(info: any) {
  fileList.value = info.fileList.slice(-1); // 只保留最新一个文件
}

// 提交导入
async function handleOk() {
  if (fileList.value.length === 0) {
    message.error('请选择要导入的Excel文件');
    return;
  }

  try {
    loading.value = true;
    
    // TODO: 实现批量导入API调用
    message.info('批量导入功能开发中，请先使用添加采购明细功能');
    
    emit('update:visible', false);
    fileList.value = [];
  } catch (error: any) {
    message.error(error.message || '批量导入失败');
  } finally {
    loading.value = false;
  }
}

// 取消导入
function handleCancel() {
  emit('update:visible', false);
  fileList.value = [];
}

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    fileList.value = [];
  }
});
</script>

<template>
  <Modal
    :open="visible"
    title="批量导入采购明细"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <div class="py-4">
      <Alert
        type="info"
        show-icon
        message="请下载模板文件，按照模板格式填写后上传"
        class="mb-4"
      />

      <div class="mb-4">
        <Button type="link" @click="() => message.info('模板下载功能开发中')">
          下载Excel导入模板
        </Button>
      </div>

      <Upload
        v-model:file-list="fileList"
        :before-upload="() => false"
        accept=".xlsx,.xls"
        @change="handleChange"
      >
        <Button>
          <UploadOutlined />
          选择Excel文件
        </Button>
      </Upload>

      <div class="mt-4 text-sm text-gray-500">
        <p class="mb-2">📝 导入说明：</p>
        <ul class="list-disc list-inside space-y-1">
          <li>支持 .xlsx 和 .xls 格式</li>
          <li>必填字段：采购单号、SKU、商品名称、数量、采购单价</li>
          <li>数量必须为正整数，单价必须为正数</li>
          <li>导入成功后将自动重新计算商品明细</li>
        </ul>
      </div>
    </div>
  </Modal>
</template>

