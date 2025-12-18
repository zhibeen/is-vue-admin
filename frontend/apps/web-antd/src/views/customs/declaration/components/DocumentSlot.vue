<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  FilePdfOutlined, 
  FileExcelOutlined, 
  FileImageOutlined, 
  FileUnknownOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  PlusOutlined,
  LoadingOutlined,
  UserOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  CloudSyncOutlined
} from '@ant-design/icons-vue';
import { Upload, message, Tooltip, Progress, Popover, Badge } from 'ant-design-vue';
import type { FileItem } from '#/api/customs/files';
import { uploadDeclarationFile } from '#/api/customs/files';
import dayjs from 'dayjs';

const props = defineProps<{
  declarationId: number;
  title: string;
  category: string;
  matchKeywords?: string[];
  file?: FileItem;
  required?: boolean;
  readonly?: boolean;
}>();

const emit = defineEmits(['refresh', 'delete', 'preview', 'download']);

const uploading = ref(false);
const uploadPercent = ref(0);

const fileExt = computed(() => props.file?.name.split('.').pop()?.toLowerCase());
const isPdf = computed(() => fileExt.value === 'pdf');
const isImage = computed(() => ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(fileExt.value || ''));

// 自动重命名并上传
const handleUpload = async (options: any) => {
  const { file, onSuccess, onError, onProgress } = options;
  uploading.value = true;
  uploadPercent.value = 0;
  
  try {
    const res = await uploadDeclarationFile(
      props.declarationId, 
      file, 
      props.category, 
      props.title, // 传 Slot 标题给后端用于重命名
      (progressEvent) => {
        if (progressEvent.total) {
           const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
           uploadPercent.value = percent;
           onProgress({ percent });
        }
      }
    );
    message.success(`${props.title} 上传成功`);
    // 直接把返回的 FileItem 传出去，更新父组件列表，而不需要整体刷新
    // emit('refresh', res); // 如果父组件支持局部更新
    emit('refresh'); // 保持原样，刷新整个列表也很快
    onSuccess(file);
  } catch (e) {
    message.error('上传失败');
    onError(e);
  } finally {
    uploading.value = false;
    uploadPercent.value = 0;
  }
};

const handleDelete = (e: Event) => {
  e.stopPropagation();
  if (props.file) {
    emit('delete', props.file);
  }
};

const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
</script>

<template>
  <div class="doc-slot flex flex-col items-center gap-2 w-full">
    <!-- 卡片主体 -->
    <div class="relative w-full aspect-square max-w-[120px] group cursor-pointer transition-all">
       
       <!-- 状态：已上传 -->
       <div v-if="file" class="w-full h-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col items-center justify-center shadow-sm overflow-hidden relative group-hover:shadow-md transition-shadow">
           <!-- 同步状态角标 -->
           <div v-if="file.status === 'missing'" class="absolute top-1 right-1 z-20">
               <Tooltip title="文件在NAS上已丢失">
                   <WarningOutlined class="text-red-500" />
               </Tooltip>
           </div>
           <div v-else-if="file.source === 'nas_sync'" class="absolute top-1 right-1 z-20">
               <Tooltip title="NAS自动同步文件">
                   <CloudSyncOutlined class="text-blue-400" />
               </Tooltip>
           </div>

           <!-- 文件信息浮窗 -->
           <Popover placement="right" title="文件详情">
               <template #content>
                   <div class="text-xs space-y-1">
                       <p><b>文件名:</b> {{ file.name }}</p>
                       <p v-if="file.slot_title"><b>类型:</b> {{ file.slot_title }}</p>
                       <p><b>大小:</b> {{ formatSize(file.size) }}</p>
                       <p><b>上传人:</b> {{ file.uploaded_by_name || 'System' }}</p>
                       <p><b>时间:</b> {{ file.created_at ? dayjs(file.created_at).format('MM-DD HH:mm') : '-' }}</p>
                       <p v-if="file.status === 'missing'" class="text-red-500"><b>状态:</b> 文件丢失</p>
                       <p v-if="file.sync_message" class="text-gray-400"><b>备注:</b> {{ file.sync_message }}</p>
                   </div>
               </template>
               <div class="absolute top-1 left-1 z-20 opacity-0 group-hover:opacity-100 transition-opacity">
                   <div class="w-4 h-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-500 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-400">
                       <UserOutlined class="text-[10px]" />
                   </div>
               </div>
           </Popover>

           <!-- 大图标 -->
           <div class="flex-1 flex items-center justify-center mt-2 transform group-hover:scale-105 transition-transform duration-300" :class="{'opacity-50 grayscale': file.status === 'missing'}">
                <FilePdfOutlined v-if="isPdf" class="text-4xl text-red-500" />
                <FileImageOutlined v-else-if="isImage" class="text-4xl text-purple-500" />
                <FileExcelOutlined v-else-if="['xls','xlsx'].includes(fileExt||'')" class="text-4xl text-green-500" />
                <FileUnknownOutlined v-else class="text-4xl text-gray-400" />
           </div>
           
           <!-- 文件名提示 -->
            <div class="w-full px-1 py-1 bg-gray-50 dark:bg-gray-700 text-[10px] text-center truncate text-gray-500 dark:text-gray-300 border-t border-gray-100 dark:border-gray-600">
                {{ file.slot_title || file.name }}
            </div>
           
           <!-- 遮罩 (hover显示) -->
           <div class="absolute inset-0 bg-black/50 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-10 backdrop-blur-[1px]">
               <template v-if="file.status !== 'missing'">
                   <Tooltip title="预览">
                       <div class="w-8 h-8 rounded-full bg-white/20 hover:bg-white/40 flex items-center justify-center cursor-pointer transition-colors" @click.stop="$emit('preview', file)">
                           <EyeOutlined class="text-white text-lg" />
                       </div>
                   </Tooltip>
                   <Tooltip title="下载">
                       <div class="w-8 h-8 rounded-full bg-white/20 hover:bg-white/40 flex items-center justify-center cursor-pointer transition-colors" @click.stop="$emit('download', file)">
                           <DownloadOutlined class="text-white text-lg" />
                       </div>
                   </Tooltip>
               </template>
               <Tooltip v-if="!readonly" title="删除">
                   <div class="w-8 h-8 rounded-full bg-red-500/20 hover:bg-red-500/60 flex items-center justify-center cursor-pointer transition-colors" @click.stop="handleDelete">
                       <DeleteOutlined class="text-white text-lg" />
                   </div>
               </Tooltip>
           </div>
       </div>

       <!-- 状态：未上传 -->
       <Upload 
         v-else
         name="file"
         :disabled="readonly"
         :showUploadList="false"
         :customRequest="handleUpload"
         accept=".pdf,.jpg,.jpeg,.png"
         class="w-full h-full block"
       >
           <div class="w-full h-full rounded-lg border border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-400 dark:hover:border-blue-500 flex flex-col items-center justify-center transition-all duration-300 text-gray-400 hover:text-blue-500 p-2 cursor-pointer group-hover:shadow-inner">
               <div v-if="uploading" class="flex flex-col items-center w-full animate-pulse">
                    <LoadingOutlined class="text-xl mb-1 text-blue-500" />
                    <span class="text-[10px] scale-90 mb-1">上传中...</span>
                    <Progress :percent="uploadPercent" size="small" :showInfo="false" status="active" :strokeColor="{ from: '#108ee9', to: '#87d068' }" class="w-10/12" />
               </div>
               <div v-else class="flex flex-col items-center" :class="{ 'opacity-50 cursor-not-allowed': readonly }">
                    <PlusOutlined class="text-2xl mb-1 transform group-hover:scale-110 transition-transform" />
                    <span class="text-xs scale-90">{{ readonly ? '只读' : '点击上传' }}</span>
               </div>
           </div>
       </Upload>

    </div>

    <!-- 底部 Label -->
    <div class="text-xs font-medium text-gray-600 dark:text-gray-400 text-center w-full truncate px-1" :title="title">
        <span v-if="required" class="text-red-500 mr-0.5">*</span>{{ title }}
    </div>
  </div>
</template>

<style scoped>
/* 覆盖 Upload 组件默认样式，使其填满容器 */
:deep(.ant-upload) {
    width: 100%;
    height: 100%;
    display: block;
}
</style>
