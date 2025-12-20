<script setup lang="ts">
/**
 * 发货单详情 - 凭证管理Tab
 * 使用通用凭证组件
 */
import { ref, onMounted } from 'vue';
import { Card } from 'ant-design-vue';
import DocumentUploader from '#/components/document/DocumentUploader.vue';
import DocumentList from '#/components/document/DocumentList.vue';
import { getDocumentsByBusiness } from '#/api/document/document';

const props = defineProps<{
  shipmentId: number;
  shipmentNo?: string;
}>();

const documents = ref<any[]>([]);
const loading = ref(false);

async function loadDocuments() {
  try {
    loading.value = true;
    documents.value = await getDocumentsByBusiness('logistics', props.shipmentId);
  } catch (e: any) {
    console.error('加载凭证失败:', e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadDocuments();
});

function handleUploadSuccess() {
  loadDocuments();
}
</script>

<template>
  <div>
    <!-- 上传区 -->
    <Card title="上传凭证" class="mb-4" :bordered="false">
      <DocumentUploader 
        business-type="logistics"
        :business-id="shipmentId"
        :business-no="shipmentNo"
        document-type="logistics_voucher"
        document-category="service_voucher"
        @success="handleUploadSuccess"
      />
    </Card>
    
    <!-- 凭证列表 -->
    <Card title="已上传凭证" :bordered="false">
      <DocumentList 
        :documents="documents" 
        :loading="loading"
        @refresh="loadDocuments" 
      />
    </Card>
  </div>
</template>

