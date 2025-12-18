<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { message, Modal, Button, Image, Tooltip, Tag } from 'ant-design-vue';
import { 
  InboxOutlined,
  ReloadOutlined,
  CloudUploadOutlined,
  FilePdfOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  WarningOutlined
} from '@ant-design/icons-vue';
import { 
  getDeclarationFiles, 
  deleteDeclarationFile, 
  getDeclarationFileUrl,
  type FileItem 
} from '#/api/customs/files';
import { checkFilesCompleteApi, type FilesCheckResult } from '#/api/customs/declaration';
import DocumentSlot from './DocumentSlot.vue';
import SmartFileUploader from './SmartFileUploader.vue';

const props = defineProps<{
  declarationId: number;
  initialFiles?: FileItem[]; // 接收预加载的文件
  requiredSlots?: string[]; // 动态必填项
  readonly?: boolean;
}>();

const fileList = ref<FileItem[]>([]);
const loading = ref(false);

// 文件完整性检查状态
const filesCheckResult = ref<FilesCheckResult | null>(null);

// 预览相关状态
const previewVisible = ref(false);
const previewUrl = ref('');
const previewTitle = ref('');
const previewType = ref<'pdf' | 'image' | 'other'>('other');

// 图片预览组件专用
const imagePreviewVisible = ref(false);
const imagePreviewUrl = ref('');

// 监听 initialFiles 变化
watch(() => props.initialFiles, (newFiles) => {
    if (newFiles) {
        fileList.value = newFiles;
    }
}, { immediate: true });

// --- 文档槽位配置 ---
// 每个分类下的具体文档槽位
const docMatrix = [
    {
        title: '关务核心单证',
        desc: '海关申报必备',
        category: '01_Customs',
        color: 'blue',
        slots: [
            { title: '报关单', keywords: ['报关单', 'Customs_Decl'], required: true },
            { title: '放行通知书', keywords: ['放行', 'Release'], required: true },
            { title: '委托报关协议', keywords: ['委托', 'Entrustment', 'Agent'], required: true },
            { title: '出口退税联', keywords: ['退税联', 'Tax_Refund'], required: true },
        ]
    },
    {
        title: '贸易全套单据',
        desc: '合同/发票/箱单',
        category: '02_Trade',
        color: 'cyan',
        slots: [
            { title: '销售合同', keywords: ['合同', 'Contract'], required: true },
            { title: '商业发票', keywords: ['发票', 'Invoice'], required: true },
            { title: '装箱单', keywords: ['装箱单', 'Packing_List'], required: true },
        ]
    },
    {
        title: '物流凭证',
        desc: '提单/CLP/装柜照',
        category: '03_Logistics',
        color: 'orange',
        slots: [
            { title: '海运/空运提单', keywords: ['提单', 'Bill'], required: true },
            { title: '订舱单', keywords: ['订舱', 'Booking'], required: false },
            { title: '散货物流发票', keywords: ['物流发票', 'Logistics_Invoice'], required: false },
            { title: '集装箱装箱单', keywords: ['集装箱装箱单', 'CLP', 'Load_Plan'], required: false },
            { title: '空柜照片', keywords: ['空柜', 'Empty_Container'], required: false },
            { title: '铅封照片', keywords: ['铅封', 'Seal'], required: false },
            { title: '封柜照片', keywords: ['封柜', 'Sealed_Container', 'Door'], required: false },
        ]
    }
];

// --- Helper Functions ---

const nasPathInfo = computed(() => {
    return `Declaration / ${props.declarationId}`;
});

// 根据分类和关键词匹配文件
const getFileForSlot = (category: string, keywords: string[]) => {
    return fileList.value.find(f => {
        // 1. 优先匹配 slot_title (如果后端正确记录)
        if (f.slot_title && keywords.some(k => f.slot_title?.includes(k))) return true;
        
        // 2. 匹配分类
        if (f.category !== category) return false;
        
        // 3. 匹配文件名关键词 (兜底)
        const name = f.name.toLowerCase();
        return keywords.some(k => name.includes(k.toLowerCase()));
    });
};

const getUncategorizedFiles = () => {
    // 找出所有未匹配到槽位的文件
    const slottedIds = new Set<number>();
    
    docMatrix.forEach(group => {
        group.slots.forEach(slot => {
            const f = getFileForSlot(group.category, slot.keywords);
            if (f) slottedIds.add(f.id);
        });
    });
    
    return fileList.value.filter(f => !slottedIds.has(f.id));
};

const loadFiles = async () => {
  if (!props.declarationId) return;
  try {
    loading.value = true;
    const res = await getDeclarationFiles(props.declarationId);
    if (Array.isArray(res)) {
       fileList.value = res;
    } else if (res && (res as any).data && Array.isArray((res as any).data)) {
       fileList.value = (res as any).data;
    } else {
       fileList.value = [];
    }
  } catch (e) {
    message.error('获取文件列表失败');
    fileList.value = [];
  } finally {
    loading.value = false;
  }
  
  // 加载完文件后，检查文件完整性
  await checkFilesComplete();
};

// 检查文件完整性
const checkFilesComplete = async () => {
  if (!props.declarationId) return;
  try {
    const result = await checkFilesCompleteApi(props.declarationId);
    filesCheckResult.value = result;
  } catch (e) {
    console.error('检查文件完整性失败:', e);
  }
};

const handleRefresh = () => {
    loadFiles();
};

const handleDelete = (file: FileItem) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除文件 ${file.name} 吗？`,
    onOk: async () => {
      try {
        await deleteDeclarationFile(props.declarationId, file.id);
        message.success('删除成功');
        fileList.value = fileList.value.filter(f => f.id !== file.id);
      } catch (e) {
        // handled
      }
    }
  });
};

const handlePreview = (file: FileItem) => {
  const ext = file.name.split('.').pop()?.toLowerCase() || '';
  const url = getDeclarationFileUrl(props.declarationId, file.id, true);
  
  if (ext === 'pdf') {
      previewType.value = 'pdf';
      previewUrl.value = url;
      previewTitle.value = file.name;
      previewVisible.value = true;
  } 
  else if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)) {
      imagePreviewUrl.value = url;
      imagePreviewVisible.value = true;
  } 
  else {
      Modal.confirm({
          title: '不支持预览',
          content: `文件 ${file.name} 暂不支持在线预览，是否直接下载？`,
          okText: '下载',
          cancelText: '取消',
          onOk: () => {
              handleDownload(file);
          }
      });
  }
};

const handleDownload = (file: FileItem) => {
  const url = getDeclarationFileUrl(props.declarationId, file.id, false);
  window.open(url, '_blank');
};

onMounted(() => {
  if (props.initialFiles && props.initialFiles.length > 0) {
      fileList.value = props.initialFiles;
  } else {
      loadFiles();
  }
});

watch(() => props.declarationId, () => {
  loadFiles();
});
</script>

<template>
  <div class="file-matrix p-6 bg-gray-50/50 dark:bg-gray-900/50 min-h-[600px]">
    
    <!-- 顶部操作栏 -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
            <h3 class="text-xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
                资料归档矩阵
                <Tag color="blue" class="font-normal text-xs px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-900">NAS Sync</Tag>
            </h3>
            <p class="text-sm text-gray-400 mt-1 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                NAS 路径: <span class="font-mono bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-400 text-xs">{{ nasPathInfo }}</span>
            </p>
        </div>
        <div class="space-x-3">
            <Button @click="handleRefresh" :loading="loading" class="shadow-sm border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
                <template #icon><ReloadOutlined /></template>
                刷新列表
            </Button>
            <!-- <Button type="primary" ghost>一键下载全部</Button> -->
        </div>
    </div>

    <!-- 文件完整性状态卡片 -->
    <div 
        v-if="filesCheckResult" 
        class="mb-6 p-4 rounded-lg border"
        :class="filesCheckResult.is_complete 
            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
            : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'"
    >
        <div class="flex items-center justify-between">
            <div class="flex items-center">
                <CheckCircleOutlined 
                    v-if="filesCheckResult.is_complete" 
                    class="text-2xl text-green-600 dark:text-green-400 mr-3"
                />
                <WarningOutlined 
                    v-else 
                    class="text-2xl text-yellow-600 dark:text-yellow-400 mr-3"
                />
                <div>
                    <div class="text-lg font-semibold" :class="filesCheckResult.is_complete ? 'text-green-700 dark:text-green-300' : 'text-yellow-700 dark:text-yellow-300'">
                        {{ filesCheckResult.is_complete ? '✓ 资料已齐全' : '⚠ 资料不齐全' }}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        已上传 {{ filesCheckResult.uploaded_slots.length }} 项，
                        必需 {{ filesCheckResult.required_slots.length }} 项
                    </div>
                </div>
            </div>
            <div v-if="!filesCheckResult.is_complete" class="text-right">
                <div class="text-sm font-medium mb-1" :class="'text-red-600 dark:text-red-400'">
                    缺少 {{ filesCheckResult.missing_count }} 项：
                </div>
                <div class="text-xs text-gray-600 dark:text-gray-400">
                    {{ filesCheckResult.missing_slots.join('、') }}
                </div>
            </div>
        </div>
    </div>

    <!-- 核心矩阵区: 响应式 Masonry 风格布局 -->
    <div class="flex flex-wrap gap-6 mb-8">
        
        <div 
            v-for="group in docMatrix" 
            :key="group.category" 
            class="flex-1 min-w-[320px] bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100/80 dark:border-gray-700 hover:shadow-md transition-all duration-300 flex flex-col"
        >
            <!-- 分组标题 -->
            <div class="flex justify-between items-center mb-5 pb-3 border-b border-gray-50 dark:border-gray-700">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="`bg-${group.color}-50 dark:bg-${group.color}-900/30 text-${group.color}-500 dark:text-${group.color}-400`">
                        <component :is="group.color === 'blue' ? InboxOutlined : (group.color === 'cyan' ? FilePdfOutlined : CloudUploadOutlined)" class="text-xl" />
                    </div>
                    <div>
                        <h4 class="font-bold text-gray-800 dark:text-gray-100 text-base leading-tight">{{ group.title }}</h4>
                        <span class="text-xs text-gray-400">{{ group.desc }}</span>
                    </div>
                </div>
            </div>
            
            <!-- 插槽网格 -->
            <div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-fr">
                <DocumentSlot 
                    v-for="slot in group.slots" 
                    :key="slot.title"
                    :declaration-id="declarationId"
                    :title="slot.title"
                    :category="group.category"
                    :matchKeywords="slot.keywords"
                    :file="getFileForSlot(group.category, slot.keywords)"
                    :required="requiredSlots ? requiredSlots.includes(slot.title) : slot.required"
                    :readonly="readonly"
                    @refresh="handleRefresh"
                    @delete="handleDelete"
                    @preview="handlePreview"
                    @download="handleDownload"
                />
            </div>
        </div>

    </div>

    <!-- 智能归档中心 (底部大通栏) -->
    <div class="bg-gradient-to-br from-white to-blue-50/30 dark:from-gray-800 dark:to-blue-900/10 rounded-xl p-6 shadow-sm border border-blue-100/50 dark:border-blue-900/30 mt-8 relative overflow-hidden">
        
        <!-- 背景装饰 -->
        <div class="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
            <ThunderboltOutlined class="text-9xl text-blue-500 transform rotate-12" />
        </div>

        <div class="flex flex-col md:flex-row gap-8 relative z-10">
            <!-- 左侧：说明与引导 -->
            <div class="md:w-1/3 flex flex-col justify-center border-r border-gray-100 dark:border-gray-700 pr-8">
                <h4 class="text-lg font-bold text-gray-800 dark:text-gray-100 mb-2 flex items-center gap-2">
                    <ThunderboltOutlined class="text-blue-500" />
                    智能归档中心
                </h4>
                <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-4">
                    支持拖入单文件或多合一 PDF。
                    <br/>
                    AI 引擎将自动识别 <span class="text-gray-700 dark:text-gray-300 font-medium">报关单、放行书、委托书</span> 并进行拆分归档。
                </p>
                
                <div class="flex gap-2">
                    <Tooltip title="支持三合一PDF自动拆分">
                        <Tag color="blue" class="border-0 bg-blue-100/50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-3 py-1">✨ 智能拆分</Tag>
                    </Tooltip>
                    <Tooltip title="NAS双向实时同步">
                        <Tag color="green" class="border-0 bg-green-100/50 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-3 py-1">🔄 自动同步</Tag>
                    </Tooltip>
                </div>
            </div>

            <!-- 右侧：文件上传与列表 -->
            <div class="md:w-2/3">
                <SmartFileUploader 
                    :files="getUncategorizedFiles()"
                    :declaration-id="declarationId"
                    category="04_Others"
                    accept=".pdf,.jpg,.jpeg,.png"
                    :disabled="readonly"
                    @refresh="handleRefresh"
                    @delete="handleDelete"
                    @preview="handlePreview"
                    @download="handleDownload"
                />
            </div>
        </div>
    </div>

    <!-- PDF 预览 Modal -->
    <Modal
      v-model:open="previewVisible"
      :title="previewTitle"
      width="80%"
      :footer="null"
      wrap-class-name="full-modal"
      destroyOnClose
      :bodyStyle="{ padding: 0, height: '80vh' }"
    >
      <iframe v-if="previewType === 'pdf'" :src="previewUrl" class="w-full h-full border-0 rounded-b-lg"></iframe>
    </Modal>

    <!-- 图片预览组件 -->
    <Image
        :width="0"
        :style="{ display: 'none' }"
        :src="imagePreviewUrl"
        :preview="{
            visible: imagePreviewVisible,
            onVisibleChange: (vis) => (imagePreviewVisible = vis),
            src: imagePreviewUrl
        }"
    />

  </div>
</template>

<style lang="less" scoped>
/* 可以在这里添加一些微动画 */
</style>