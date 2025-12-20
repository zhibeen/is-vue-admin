<script setup lang="ts">
/**
 * 凭证预览组件
 * 支持PDF、图片预览
 */
import { Modal, Image } from 'ant-design-vue';
import { computed } from 'vue';
import type { DocumentCenter } from '#/api/document/document';

const props = defineProps<{
  visible: boolean;
  document: DocumentCenter;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

// 判断是否为图片
const isImage = computed(() => {
  const imageTypes = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
  return imageTypes.includes(props.document.file_type?.toLowerCase() || '');
});

// 判断是否为PDF
const isPDF = computed(() => {
  return props.document.file_type?.toLowerCase() === '.pdf';
});

// 文件URL（实际项目中应该是真实的URL）
const fileUrl = computed(() => {
  return props.document.file_url || props.document.file_path;
});

function handleClose() {
  emit('close');
}
</script>

<template>
  <Modal
    :open="visible"
    :title="`预览: ${document.file_name}`"
    width="80%"
    :footer="null"
    @cancel="handleClose"
  >
    <div class="preview-container" style="min-height: 500px;">
      <!-- 图片预览 -->
      <div v-if="isImage" class="flex justify-center">
        <Image 
          :src="fileUrl" 
          :alt="document.file_name"
          :preview="false"
          style="max-width: 100%; max-height: 600px;"
        />
      </div>
      
      <!-- PDF预览 -->
      <div v-else-if="isPDF" style="height: 600px;">
        <iframe
          :src="fileUrl"
          style="width: 100%; height: 100%; border: none;"
          title="PDF预览"
        />
      </div>
      
      <!-- 其他文件类型 -->
      <div v-else class="flex flex-col items-center justify-center" style="height: 400px;">
        <p class="text-gray-500 text-lg mb-4">
          暂不支持预览此类型文件
        </p>
        <p class="text-gray-400">
          文件类型: {{ document.file_type }}
        </p>
        <p class="text-gray-400">
          文件大小: {{ (document.file_size! / 1024).toFixed(2) }} KB
        </p>
        <a-button 
          type="primary" 
          class="mt-4"
          @click="handleClose"
        >
          关闭
        </a-button>
      </div>
    </div>
    
    <!-- 文件信息 -->
    <div class="mt-4 p-4 bg-gray-50 rounded">
      <div class="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span class="text-gray-600">文件名:</span>
          <span class="ml-2 font-medium">{{ document.file_name }}</span>
        </div>
        <div>
          <span class="text-gray-600">文件类型:</span>
          <span class="ml-2">{{ document.file_type }}</span>
        </div>
        <div>
          <span class="text-gray-600">上传时间:</span>
          <span class="ml-2">{{ new Date(document.uploaded_at).toLocaleString('zh-CN') }}</span>
        </div>
        <div>
          <span class="text-gray-600">文件大小:</span>
          <span class="ml-2">{{ (document.file_size! / 1024).toFixed(2) }} KB</span>
        </div>
        <div v-if="document.document_category">
          <span class="text-gray-600">文档分类:</span>
          <span class="ml-2">{{ document.document_category }}</span>
        </div>
        <div>
          <span class="text-gray-600">审核状态:</span>
          <a-tag 
            :color="document.audit_status === 'approved' ? 'success' : 'default'"
            class="ml-2"
          >
            {{ document.audit_status === 'approved' ? '已审核' : '待审核' }}
          </a-tag>
        </div>
      </div>
    </div>
  </Modal>
</template>

<style scoped>
.preview-container {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

