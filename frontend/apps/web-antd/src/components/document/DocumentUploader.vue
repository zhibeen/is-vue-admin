<script setup lang="ts">
/**
 * 通用凭证上传组件
 * 支持拖拽、多文件、预览、删除
 */
import { Upload, message } from 'ant-design-vue';
import { InboxOutlined } from '@ant-design/icons-vue';
import { ref } from 'vue';
import { uploadDocument } from '#/api/document/document';

const props = defineProps<{
  businessType: string;  // logistics/purchase/customs/payment
  businessId: number;
  businessNo?: string;
  documentType?: string;
  documentCategory?: string;
  maxCount?: number;  // 最大文件数
}>();

const emit = defineEmits<{
  (e: 'success', file: any): void;
  (e: 'error', error: any): void;
}>();

const fileList = ref<any[]>([]);
const uploading = ref(false);

// 上传配置
const uploadProps = {
  name: 'file',
  multiple: props.maxCount ? props.maxCount > 1 : true,
  accept: '.pdf,.jpg,.jpeg,.png,.xlsx,.xls,.doc,.docx',
  maxCount: props.maxCount || 10,
  beforeUpload: (file: File) => {
    // 文件大小限制 10MB
    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('文件大小不能超过10MB');
      return false;
    }
    
    // 文件类型检查
    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      message.error('只支持 PDF、图片、Excel、Word 格式');
      return false;
    }
    
    return true;
  },
  customRequest: async (options: any) => {
    try {
      uploading.value = true;
      
      const formData = new FormData();
      formData.append('file', options.file);
      formData.append('business_type', props.businessType);
      formData.append('business_id', String(props.businessId));
      
      if (props.businessNo) {
        formData.append('business_no', props.businessNo);
      }
      if (props.documentType) {
        formData.append('document_type', props.documentType);
      }
      if (props.documentCategory) {
        formData.append('document_category', props.documentCategory);
      }
      
      const result = await uploadDocument(formData);
      
      message.success(`${options.file.name} 上传成功`);
      options.onSuccess(result);
      emit('success', result);
    } catch (error: any) {
      message.error(`${options.file.name} 上传失败: ${error.message || '未知错误'}`);
      options.onError(error);
      emit('error', error);
    } finally {
      uploading.value = false;
    }
  },
  onChange(info: any) {
    let newFileList = [...info.fileList];
    
    // 只显示最近上传的文件
    newFileList = newFileList.slice(-props.maxCount! || -10);
    
    // 读取响应并显示文件链接
    newFileList = newFileList.map(file => {
      if (file.response) {
        file.url = file.response.file_url;
      }
      return file;
    });
    
    fileList.value = newFileList;
  },
  onRemove(file: any) {
    const index = fileList.value.indexOf(file);
    const newFileList = fileList.value.slice();
    newFileList.splice(index, 1);
    fileList.value = newFileList;
  },
};
</script>

<template>
  <div>
    <Upload.Dragger 
      v-bind="uploadProps" 
      :file-list="fileList"
      :disabled="uploading"
    >
      <p class="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p class="ant-upload-hint">
        支持 PDF、图片、Excel、Word 格式，单个文件不超过10MB
        <span v-if="maxCount">，最多上传{{ maxCount }}个文件</span>
      </p>
    </Upload.Dragger>
  </div>
</template>

