<script setup lang="ts">
/**
 * 通用凭证列表组件
 * 展示凭证列表，支持预览、下载、删除、审核
 */
import { ref, computed } from 'vue';
import { Table, Tag, Space, Button, Popconfirm, message, Image } from 'ant-design-vue';
import { 
  FileTextOutlined, 
  FilePdfOutlined, 
  FileExcelOutlined, 
  FileImageOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons-vue';
import { deleteDocument, type DocumentCenter } from '#/api/document/document';
import DocumentPreview from './DocumentPreview.vue';

const props = defineProps<{
  documents: DocumentCenter[];
  loading?: boolean;
  showActions?: boolean;
  showAudit?: boolean;
}>();

const emit = defineEmits<{
  (e: 'refresh'): void;
  (e: 'audit', document: DocumentCenter): void;
}>();

// 预览
const previewVisible = ref(false);
const previewDocument = ref<DocumentCenter | null>(null);

// 表格列定义
const columns = [
  {
    title: '文件名',
    dataIndex: 'file_name',
    key: 'file_name',
    width: 250,
    ellipsis: true,
  },
  {
    title: '类型',
    dataIndex: 'file_type',
    key: 'file_type',
    width: 80,
  },
  {
    title: '分类',
    dataIndex: 'document_category',
    key: 'document_category',
    width: 120,
  },
  {
    title: '大小',
    dataIndex: 'file_size',
    key: 'file_size',
    width: 100,
  },
  {
    title: '上传时间',
    dataIndex: 'uploaded_at',
    key: 'uploaded_at',
    width: 160,
  },
  {
    title: '审核状态',
    dataIndex: 'audit_status',
    key: 'audit_status',
    width: 100,
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right',
  },
];

// 获取文件图标
function getFileIcon(fileType: string) {
  const type = fileType?.toLowerCase();
  if (type === '.pdf') return FilePdfOutlined;
  if (['.xlsx', '.xls'].includes(type)) return FileExcelOutlined;
  if (['.jpg', '.jpeg', '.png'].includes(type)) return FileImageOutlined;
  return FileTextOutlined;
}

// 获取文件图标颜色
function getFileIconColor(fileType: string) {
  const type = fileType?.toLowerCase();
  if (type === '.pdf') return '#f5222d';
  if (['.xlsx', '.xls'].includes(type)) return '#52c41a';
  if (['.jpg', '.jpeg', '.png'].includes(type)) return '#1890ff';
  return '#8c8c8c';
}

// 格式化文件大小
function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// 格式化日期
function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
}

// 获取审核状态
function getAuditStatusTag(status: string) {
  const map: Record<string, { color: string; text: string }> = {
    pending: { color: 'default', text: '待审核' },
    approved: { color: 'success', text: '已通过' },
    rejected: { color: 'error', text: '已驳回' },
  };
  return map[status] || { color: 'default', text: status };
}

// 获取文档分类文本
function getDocumentCategoryText(category: string | undefined): string {
  const map: Record<string, string> = {
    service_voucher: '服务凭证',
    payment_voucher: '付款凭证',
    contract_voucher: '合同凭证',
    invoice_voucher: '发票凭证',
    customs_voucher: '报关凭证',
  };
  return map[category || ''] || category || '-';
}

// 预览文件
function handlePreview(record: DocumentCenter) {
  previewDocument.value = record;
  previewVisible.value = true;
}

// 下载文件
function handleDownload(record: DocumentCenter) {
  // TODO: 实现文件下载
  message.info('下载功能开发中');
}

// 删除文件
async function handleDelete(record: DocumentCenter) {
  try {
    await deleteDocument(record.id);
    message.success('删除成功');
    emit('refresh');
  } catch (e: any) {
    message.error('删除失败: ' + (e.message || '未知错误'));
  }
}

// 审核
function handleAudit(record: DocumentCenter) {
  emit('audit', record);
}
</script>

<template>
  <div>
    <Table
      :columns="columns"
      :data-source="documents"
      :loading="loading"
      :pagination="{ pageSize: 10 }"
      :scroll="{ x: 1000 }"
      size="small"
    >
      <!-- 文件名列 -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'file_name'">
          <Space>
            <component 
              :is="getFileIcon(record.file_type)" 
              :style="{ color: getFileIconColor(record.file_type), fontSize: '20px' }"
            />
            <span class="font-medium">{{ record.file_name }}</span>
          </Space>
        </template>
        
        <!-- 文件类型列 -->
        <template v-else-if="column.key === 'file_type'">
          <Tag>{{ record.file_type || '-' }}</Tag>
        </template>
        
        <!-- 分类列 -->
        <template v-else-if="column.key === 'document_category'">
          {{ getDocumentCategoryText(record.document_category) }}
        </template>
        
        <!-- 文件大小列 -->
        <template v-else-if="column.key === 'file_size'">
          {{ formatFileSize(record.file_size) }}
        </template>
        
        <!-- 上传时间列 -->
        <template v-else-if="column.key === 'uploaded_at'">
          {{ formatDate(record.uploaded_at) }}
        </template>
        
        <!-- 审核状态列 -->
        <template v-else-if="column.key === 'audit_status'">
          <Tag :color="getAuditStatusTag(record.audit_status).color">
            {{ getAuditStatusTag(record.audit_status).text }}
          </Tag>
        </template>
        
        <!-- 操作列 -->
        <template v-else-if="column.key === 'action'">
          <Space>
            <Button 
              type="link" 
              size="small"
              @click="handlePreview(record)"
            >
              <template #icon><EyeOutlined /></template>
              预览
            </Button>
            
            <Button 
              type="link" 
              size="small"
              @click="handleDownload(record)"
            >
              <template #icon><DownloadOutlined /></template>
              下载
            </Button>
            
            <Button 
              v-if="showAudit && record.audit_status === 'pending'"
              type="link" 
              size="small"
              @click="handleAudit(record)"
            >
              审核
            </Button>
            
            <Popconfirm
              v-if="showActions !== false && !record.archived"
              title="确认删除此凭证？"
              ok-text="确认"
              cancel-text="取消"
              @confirm="handleDelete(record)"
            >
              <Button 
                type="link" 
                danger 
                size="small"
              >
                <template #icon><DeleteOutlined /></template>
                删除
              </Button>
            </Popconfirm>
          </Space>
        </template>
      </template>
    </Table>
    
    <!-- 预览弹窗 -->
    <DocumentPreview
      v-if="previewVisible && previewDocument"
      :visible="previewVisible"
      :document="previewDocument"
      @close="previewVisible = false"
    />
  </div>
</template>

