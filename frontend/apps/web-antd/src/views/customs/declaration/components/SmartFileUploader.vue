<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { 
  FilePdfOutlined, 
  FileExcelOutlined, 
  FileWordOutlined,
  FileImageOutlined, 
  FilePptOutlined,
  FileTextOutlined,
  FileZipOutlined,
  FileUnknownOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  CloudUploadOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue';
import { Upload, message, Tooltip, Progress } from 'ant-design-vue';
import type { FileItem } from '#/api/customs/files';
import { uploadDeclarationFile } from '#/api/customs/files';

interface UploadingItem {
  uid: string;
  name: string;
  percent: number;
  status: 'uploading' | 'done' | 'error';
  errorMsg?: string;
  file?: File;
}

const props = withDefaults(defineProps<{
  files: FileItem[];
  declarationId: number;
  category?: string;
  multiple?: boolean;
  accept?: string;
  disabled?: boolean;
}>(), {
  files: () => [],
  category: '04_Others',
  multiple: true,
  disabled: false
});

const emit = defineEmits(['update:files', 'refresh', 'delete', 'preview', 'download']);

// 本地维护的正在上传的文件列表
const uploadingFiles = ref<UploadingItem[]>([]);

const displayFiles = computed(() => {
    // 1. 获取现有文件的唯一标识集合
    const existingNames = new Set(props.files.map(f => f.name));

    // 2. 过滤掉已经存在于 props.files 中的 uploadingFiles
    const activeUploads = uploadingFiles.value.filter(u => !existingNames.has(u.name));

    return {
        existing: props.files,
        uploading: activeUploads
    };
});

// 监听 props.files 变化，清理已完成的上传项 (作为双重保障)
watch(() => props.files, (newFiles) => {
    const existingNames = new Set(newFiles.map(f => f.name));
    if (uploadingFiles.value.length > 0) {
        uploadingFiles.value = uploadingFiles.value.filter(u => !existingNames.has(u.name));
    }
}, { deep: true });

const getFileExt = (filename: string) => filename.split('.').pop()?.toLowerCase() || '';

const isPdf = (ext: string) => ext === 'pdf';
const isImage = (ext: string) => ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext);
const isExcel = (ext: string) => ['xls', 'xlsx', 'csv'].includes(ext);
const isWord = (ext: string) => ['doc', 'docx'].includes(ext);
const isPpt = (ext: string) => ['ppt', 'pptx'].includes(ext);
const isZip = (ext: string) => ['zip', 'rar', '7z', 'tar', 'gz'].includes(ext);
const isText = (ext: string) => ['txt', 'md', 'json', 'xml', 'log'].includes(ext);

const handleUpload = async (options: any) => {
  const { file, onSuccess, onError, onProgress } = options;
  
  // Check 1: 单文件模式限制
  if (!props.multiple && props.files.length > 0) {
      message.warning('仅允许上传单个文件');
      return;
  }

  // Check 2: 重名检测 (针对问题一)
  // 如果文件名已存在，提示用户 (但允许覆盖，或根据需求 return 阻止)
  const isDuplicate = props.files.some(f => f.name === file.name);
  if (isDuplicate) {
      message.info(`即将覆盖已存在的文件: ${file.name}`);
  }

  const uploadItem: UploadingItem = {
      uid: file.uid || Math.random().toString(36).substring(2),
      name: file.name,
      percent: 0,
      status: 'uploading',
      file: file
  };
  
  uploadingFiles.value.push(uploadItem);
  
  try {
    await uploadDeclarationFile(
      props.declarationId, 
      file, 
      props.category, 
      undefined, 
      (progressEvent) => {
        if (progressEvent.total) {
           const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
           const item = uploadingFiles.value.find(u => u.uid === uploadItem.uid);
           if (item) {
               item.percent = percent;
           }
           onProgress({ percent });
        }
      }
    );
    
    // 上传成功
    const item = uploadingFiles.value.find(u => u.uid === uploadItem.uid);
    if (item) {
        item.status = 'done';
        item.percent = 100;

        // --- FIX (针对问题二): 延迟移除已完成的项 ---
        // 确保 "完成" 状态显示一会后自动消失。
        // 这样即使文件被归档到了其他 Slot (不在当前 props.files 里)，
        // 这个临时的 Upload Item 也会消失，不会卡在 Checkmark 状态。
        setTimeout(() => {
            uploadingFiles.value = uploadingFiles.value.filter(u => u.uid !== uploadItem.uid);
        }, 1500);
    }
    
    message.success(`${file.name} 上传成功`);
    emit('refresh'); 
    onSuccess(file);
    
  } catch (e: any) {
    const item = uploadingFiles.value.find(u => u.uid === uploadItem.uid);
    if (item) {
        item.status = 'error';
        item.errorMsg = e.message || '上传失败';
    }
    message.error(`${file.name} 上传失败`);
    onError(e);
  }
};

const handleDelete = (file: FileItem) => {
  emit('delete', file);
};

const handleCancelUpload = (uid: string) => {
    uploadingFiles.value = uploadingFiles.value.filter(u => u.uid !== uid);
};

const handlePreview = (file: FileItem) => {
    emit('preview', file);
};

const handleDownload = (file: FileItem) => {
    emit('download', file);
};
</script>

<template>
  <div class="smart-file-uploader flex flex-wrap gap-4">
    
    <!-- 1. 已存在的正式文件列表 -->
    <div 
        v-for="(file, index) in displayFiles.existing" 
        :key="file.path || file.name || index" 
        class="relative w-[100px] h-[100px] group cursor-pointer transition-all"
    >
       <div class="w-full h-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col items-center justify-center shadow-sm overflow-hidden relative hover:shadow-md transition-shadow">
           <!-- 大图标 -->
           <div class="flex-1 flex items-center justify-center mt-2">
                <FilePdfOutlined v-if="isPdf(getFileExt(file.name))" class="text-4xl text-red-500" />
                <FileImageOutlined v-else-if="isImage(getFileExt(file.name))" class="text-4xl text-purple-500" />
                <FileExcelOutlined v-else-if="isExcel(getFileExt(file.name))" class="text-4xl text-green-500" />
                <FileWordOutlined v-else-if="isWord(getFileExt(file.name))" class="text-4xl text-blue-500" />
                <FilePptOutlined v-else-if="isPpt(getFileExt(file.name))" class="text-4xl text-orange-500" />
                <FileZipOutlined v-else-if="isZip(getFileExt(file.name))" class="text-4xl text-yellow-600" />
                <FileTextOutlined v-else-if="isText(getFileExt(file.name))" class="text-4xl text-gray-500 dark:text-gray-400" />
                <FileUnknownOutlined v-else class="text-4xl text-gray-400" />
           </div>
           
           <!-- 文件名 -->
            <div class="w-full px-1 py-1 bg-gray-50 dark:bg-gray-700 text-[10px] text-center truncate text-gray-500 dark:text-gray-300 border-t border-gray-100 dark:border-gray-600" :title="file.name">
                {{ file.name }}
            </div>
           
           <!-- 遮罩操作区 -->
           <div class="absolute inset-0 bg-black/50 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
               <Tooltip title="预览">
                   <EyeOutlined class="text-white text-lg hover:scale-110 cursor-pointer p-1" @click.stop="handlePreview(file)" />
               </Tooltip>
               <Tooltip title="下载">
                   <DownloadOutlined class="text-white text-lg hover:scale-110 cursor-pointer p-1" @click.stop="handleDownload(file)" />
               </Tooltip>
               <Tooltip v-if="!disabled" title="删除">
                   <DeleteOutlined class="text-white text-lg hover:scale-110 cursor-pointer p-1" @click.stop="handleDelete(file)" />
               </Tooltip>
           </div>
       </div>
    </div>

    <!-- 2. 正在上传/处理中的文件列表 (乐观更新) -->
    <div 
        v-for="item in displayFiles.uploading" 
        :key="item.uid" 
        class="relative w-[100px] h-[100px] group transition-all"
    >
       <div class="w-full h-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col items-center justify-center shadow-sm overflow-hidden relative">
           
           <!-- 上传中状态 -->
           <div v-if="item.status === 'uploading'" class="flex flex-col items-center justify-center w-full px-2">
               <LoadingOutlined class="text-2xl text-blue-500 mb-2" />
               <Progress :percent="item.percent" size="small" :showInfo="false" status="active" :strokeColor="{ from: '#108ee9', to: '#87d068' }" class="w-full" />
               <span class="text-[10px] text-gray-400 mt-1 scale-90 truncate w-full text-center">{{ item.name }}</span>
           </div>

           <!-- 成功状态 -->
           <div v-else-if="item.status === 'done'" class="flex flex-col items-center justify-center w-full h-full">
                <!-- 临时显示图标 -->
                <div class="flex-1 flex items-center justify-center mt-2 opacity-50">
                    <FilePdfOutlined v-if="isPdf(getFileExt(item.name))" class="text-4xl text-red-500" />
                    <FileImageOutlined v-else-if="isImage(getFileExt(item.name))" class="text-4xl text-purple-500" />
                    <FileUnknownOutlined v-else class="text-4xl text-gray-400" />
                </div>
                <div class="absolute inset-0 flex items-center justify-center">
                    <CheckCircleOutlined class="text-2xl text-green-500 bg-white dark:bg-gray-800 rounded-full shadow-sm" />
                </div>
                <div class="w-full px-1 py-1 bg-gray-50 dark:bg-gray-700 text-[10px] text-center truncate text-gray-500 dark:text-gray-300 border-t border-gray-100 dark:border-gray-600">
                    {{ item.name }}
                </div>
           </div>

           <!-- 错误状态 -->
           <div v-else-if="item.status === 'error'" class="flex flex-col items-center justify-center w-full h-full text-red-500">
                <ExclamationCircleOutlined class="text-2xl mb-1" />
                <span class="text-[10px] text-center px-1">上传失败</span>
                <Tooltip title="移除">
                    <DeleteOutlined class="absolute top-1 right-1 cursor-pointer text-gray-400 hover:text-red-500" @click="handleCancelUpload(item.uid)" />
                </Tooltip>
           </div>

       </div>
    </div>

    <!-- 3. 上传按钮 -->
    <!-- 始终显示在最后，除非 disabled 或 单选已满 -->
    <div 
        v-if="!disabled && (multiple || props.files.length === 0)"
        class="w-[100px] h-[100px]"
    >
        <Upload 
            name="file"
            :showUploadList="false"
            :customRequest="handleUpload"
            :multiple="multiple"
            :accept="accept"
            class="w-full h-full block"
        >
            <div class="w-full h-full rounded-lg border border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-400 dark:hover:border-blue-500 flex flex-col items-center justify-center transition-colors text-gray-400 hover:text-blue-500 cursor-pointer">
                <div class="flex flex-col items-center">
                    <CloudUploadOutlined class="text-2xl mb-1" />
                    <span class="text-xs scale-90">上传文件</span>
                </div>
            </div>
        </Upload>
    </div>

  </div>
</template>

<style scoped>
:deep(.ant-upload) {
    width: 100%;
    height: 100%;
    display: block;
}
</style>
