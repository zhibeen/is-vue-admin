<script setup lang="ts">
import { useRoute } from 'vue-router';
import { onMounted, ref, computed } from 'vue';
import { Page } from '@vben/common-ui';
import { Tabs, Button, Space, Card, message, Select, Textarea, Modal, Tag, Dropdown, Menu, Checkbox, Radio } from 'ant-design-vue';
import { getDeclarationDetailApi, updateDeclarationApi, getAllowedTransitionsApi, changeDeclarationStatusApi, downloadDeclarationPdfApi, checkFilesCompleteApi, type AllowedTransitionsResponse, type FilesCheckResult } from '#/api/customs/declaration';
import { getDeclarationFiles, type FileItem } from '#/api/customs/files';
import { type TaxCustomsDeclaration } from '#/api/customs/declaration';
import { getDictItemsApi, type DictItem } from '#/api/system/dict';
import DeclarationFilePanel from './components/DeclarationFilePanel.vue';
import DeclarationTab from './components/DeclarationTab.vue';
import PackingTab from './components/PackingTab.vue';
import InvoiceTab from './components/InvoiceTab.vue';
import ContractTab from './components/ContractTab.vue';
import ProxyTab from './components/ProxyTab.vue';
import { useDeclarationConfig, docTypes, getUnitName } from './declaration.config';
import { getCompanyList } from '#/api/serc/foundation';
import { getOverseasConsigneeList, type OverseasConsignee } from '#/api/customs/consignee';
import type { SysCompany } from '#/api/serc/model';
import { 
    EditOutlined, 
    DownloadOutlined, 
    LinkOutlined,
    PaperClipOutlined,
    SaveOutlined,
    CloseOutlined,
    SendOutlined,
    FileOutlined,
    AuditOutlined,
    CheckCircleOutlined,
    ContainerOutlined,
    WarningOutlined,
    FileDoneOutlined,
    RightOutlined
} from '@ant-design/icons-vue';

const route = useRoute();
const loading = ref(false);
const detail = ref<TaxCustomsDeclaration>({} as TaxCustomsDeclaration);
const fileList = ref<FileItem[]>([]); // 预加载文件列表
const activeTab = ref('declaration');

const id = computed(() => route.params.id as string);

async function loadData() {
  if (!id.value) return;
  try {
    loading.value = true;
    
    // 并行请求：获取详情 + 预加载文件
    const [detailRes, filesRes] = await Promise.all([
      getDeclarationDetailApi(Number(id.value)),
      getDeclarationFiles(Number(id.value))
    ]);
    
    detail.value = detailRes;
    
    // 处理文件列表响应 (兼容逻辑)
    if (Array.isArray(filesRes)) {
       fileList.value = filesRes;
    } else if (filesRes && (filesRes as any).data && Array.isArray((filesRes as any).data)) {
       fileList.value = (filesRes as any).data;
    } else {
       fileList.value = [];
    }
    
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
  
  // 检查文件完整性（用于前端提示）
  await checkFilesComplete();
}

// 模拟文档类型选中状态
// const docTypes = ['报关单', '装箱单', '发票', '申报要素', '合同', '委托书'];

const isEditMode = ref(false);
const submitting = ref(false);

// 计算页面标题 - 显示预录入编号便于识别
const pageTitle = computed(() => {
    return detail.value.pre_entry_no || '报关单详情';
});

const countryOptions = ref<DictItem[]>([]);
const portOptions = ref<DictItem[]>([]);
const transactionModeOptions = ref<DictItem[]>([]);
const tradeModeOptions = ref<DictItem[]>([]);
const natureOfExemptionOptions = ref<DictItem[]>([]);
const transportModeOptions = ref<DictItem[]>([]);
const currencyOptions = ref<DictItem[]>([]);
const companyOptions = ref<SysCompany[]>([]);
const consigneeOptions = ref<OverseasConsignee[]>([]);

// 状态流转相关
const allowedTransitions = ref<AllowedTransitionsResponse | null>(null);
const statusChanging = ref(false);
const amendmentReason = ref('');
const amendmentModalVisible = ref(false);
const pendingStatusChange = ref<{ status: string; description: string } | null>(null);

// 下载相关
const downloadModalVisible = ref(false);
const downloadLoading = ref(false);
const selectedDownloadItems = ref<string[]>(['declaration']); // 默认选中报关单
const downloadMode = ref<'merged' | 'separate'>('merged'); // 下载模式：合并/分别

// 文件完整性检查
const filesCheckResult = ref<FilesCheckResult | null>(null);
const filesChecking = ref(false);

// 可下载的资料类型配置（归档资料已独立为单独按钮）
const downloadOptions = [
    { label: '报关单', value: 'declaration', description: '包含报关单主表及商品明细（含申报要素）' },
    { label: '装箱单', value: 'packing', description: '包含装箱明细信息' },
    { label: '发票', value: 'invoice', description: '包含发票信息' },
    { label: '合同', value: 'contract', description: '包含合同信息' },
    { label: '委托书', value: 'proxy', description: '包含委托书信息' }
];

// 状态流程配置（标准流程）
const statusFlow = [
    { value: 'draft', label: '草稿', icon: FileOutlined, color: 'text-gray-500', bgColor: 'bg-gray-100 dark:bg-gray-800' },
    { value: 'pending', label: '待审核', icon: AuditOutlined, color: 'text-blue-500', bgColor: 'bg-blue-50 dark:bg-blue-900/30' },
    { value: 'declared', label: '已申报', icon: SendOutlined, color: 'text-orange-500', bgColor: 'bg-orange-50 dark:bg-orange-900/30' },
    { value: 'cleared', label: '已放行', icon: CheckCircleOutlined, color: 'text-green-500', bgColor: 'bg-green-50 dark:bg-green-900/30' },
    { value: 'archived', label: '已归档', icon: ContainerOutlined, color: 'text-cyan-500', bgColor: 'bg-cyan-50 dark:bg-cyan-900/30' },
];

// 异常状态配置
const exceptionStatus = [
    { value: 'amending', label: '修撤中', icon: WarningOutlined, color: 'text-red-500', bgColor: 'bg-red-50 dark:bg-red-900/30' },
    { value: 'amended', label: '修改已批准', icon: FileDoneOutlined, color: 'text-purple-500', bgColor: 'bg-purple-50 dark:bg-purple-900/30' },
];

// 计算当前状态在流程中的位置
const currentStepIndex = computed(() => {
    return statusFlow.findIndex(s => s.value === detail.value.status);
});

// 判断是否为异常状态
const isExceptionStatus = computed(() => {
    return exceptionStatus.some(s => s.value === detail.value.status);
});

// 获取当前状态配置
const currentStatusConfig = computed(() => {
    return [...statusFlow, ...exceptionStatus].find(s => s.value === detail.value.status);
});

async function loadDictionaries() {
    try {
        const [
            cRes, 
            pRes, 
            transRes, 
            tradeRes, 
            natureRes, 
            transportRes, 
            currencyRes,
            compRes, 
            consRes
        ] = await Promise.allSettled([
            getDictItemsApi('country'),
            getDictItemsApi('port'),
            getDictItemsApi('transaction_mode'),
            getDictItemsApi('trade_mode'),
            getDictItemsApi('nature_of_exemption'),
            getDictItemsApi('transport_mode'),
            getDictItemsApi('currency'),
            getCompanyList(),
            getOverseasConsigneeList()
        ]);
        
        if (cRes.status === 'fulfilled') countryOptions.value = cRes.value;
        if (pRes.status === 'fulfilled') portOptions.value = pRes.value;
        if (transRes.status === 'fulfilled') transactionModeOptions.value = transRes.value;
        if (tradeRes.status === 'fulfilled') tradeModeOptions.value = tradeRes.value;
        if (natureRes.status === 'fulfilled') natureOfExemptionOptions.value = natureRes.value;
        if (transportRes.status === 'fulfilled') transportModeOptions.value = transportRes.value;
        if (currencyRes.status === 'fulfilled') currencyOptions.value = currencyRes.value;
        if (compRes.status === 'fulfilled') companyOptions.value = compRes.value;
        if (consRes.status === 'fulfilled') consigneeOptions.value = consRes.value;

    } catch (e) {
        console.error('Dict load failed', e);
    }
}

// 计算 FOB 单价 (基于总价分摊运保费)
function calculateFobUnitPrice(item: any, header: TaxCustomsDeclaration) {
    // 1. 获取扣除项 (运费+保费+杂费)
    // 简单处理：假设这些字段存储的是纯数字或 "USD/200/3" 格式，这里暂按纯数字处理或解析第一部分
    const parseCost = (val: string | undefined) => {
        if (!val) return 0;
        // 尝试提取数字
        const match = val.toString().match(/(\d+(\.\d+)?)/);
        return match ? parseFloat(match[0]) : 0;
    };

    const freight = parseCost(header.freight);
    const insurance = parseCost(header.insurance);
    const incidental = parseCost(header.incidental);
    const totalDeductible = freight + insurance + incidental;
    
    // 如果没有扣除项，且成交方式是 FOB，则直接返回单价
    if (totalDeductible <= 0) return Number(item.usd_unit_price).toFixed(4);

    // 2. 计算分摊比例 (该商品总价 / 所有商品总价)
    const allItemsTotal = header.items?.reduce((sum, i) => sum + Number(i.usd_total), 0) || 1;
    const ratio = Number(item.usd_total) / allItemsTotal;
    
    // 3. 计算该商品的扣除额
    const itemDeductible = totalDeductible * ratio;
    
    // 4. 计算 FOB 总价
    const itemFobTotal = Number(item.usd_total) - itemDeductible;

    // 5. 计算 FOB 单价
    const qty = Number(item.qty) || 1;
    return (itemFobTotal / qty).toFixed(4);
}

async function handleSave() {
    if (!detail.value.id) return;

    // --- 表单验证 ---
    const errors: string[] = [];
    
    detail.value.items?.forEach((item, index) => {
        const lineNo = index + 1;
        // 1. 净重 <= 毛重
        if (item.net_weight && item.gross_weight && Number(item.net_weight) > Number(item.gross_weight)) {
            errors.push(`第 ${lineNo} 行: 净重 (${item.net_weight}) 不能大于毛重 (${item.gross_weight})`);
        }
        
        // 2. 整数校验 (个/套)
        // 007=个, 006=套
        // (InputNumber 的 precision 已做限制，此处仅作为双重保障)
        if (['007', '006', '001', '012', '011', '015', '008', '120'].includes(item.unit) && !Number.isInteger(Number(item.qty))) {
             errors.push(`第 ${lineNo} 行: 单位为'${getUnitName(item.unit)}'时，数量必须为整数`);
        }
        
        // 3. 总价校验 (单价*数量 = 总价, 允许 0.05 误差)
        const calcTotal = Number(item.qty) * Number(item.usd_unit_price);
        const diff = Math.abs(calcTotal - Number(item.usd_total));
        if (diff > 0.05) {
             errors.push(`第 ${lineNo} 行: 总价校验失败 (计算值: ${calcTotal.toFixed(2)}, 当前值: ${item.usd_total})`);
        }
    });

    if (errors.length > 0) {
        // 显示前3条错误
        message.error(errors.slice(0, 3).join('; '));
        return;
    }
    // --- 验证结束 ---

    try {
        submitting.value = true;
        // 简单处理：确保数字字段类型正确
        const payload = { ...detail.value };
        if (payload.pack_count) payload.pack_count = Number(payload.pack_count);
        if (payload.gross_weight) payload.gross_weight = Number(payload.gross_weight);
        if (payload.net_weight) payload.net_weight = Number(payload.net_weight);
        
        await updateDeclarationApi(detail.value.id, payload);
        message.success('保存成功');
        isEditMode.value = false;
        loadData();
    } catch (e) {
        console.error(e);
        // message.error 由 request 拦截器处理，或在此补充
    } finally {
        submitting.value = false;
    }
}

function handleCancel() {
    isEditMode.value = false;
    loadData(); // 还原数据
}

function handleEnterEdit() {
    isEditMode.value = true;
    message.info('已进入编辑模式');
}

// 加载允许的状态转换
async function loadAllowedTransitions() {
    if (!id.value) return;
    try {
        const res = await getAllowedTransitionsApi(Number(id.value));
        allowedTransitions.value = res;
    } catch (e) {
        console.error('Failed to load allowed transitions', e);
    }
}

// 处理状态变更
async function handleStatusChange(newStatus: string, description: string) {
    if (!id.value) return;
    
    // 如果是修撤操作，需要输入原因
    if (newStatus === 'amending') {
        amendmentReason.value = '';
        pendingStatusChange.value = { status: newStatus, description };
        amendmentModalVisible.value = true;
        return;
    }
    
    // 如果是归档操作，需要先检查文件完整性
    if (newStatus === 'archived') {
        const checkResult = await checkFilesComplete();
        if (!checkResult || !checkResult.is_complete) {
            // 显示详细的缺失文件信息
            const missingFilesList = checkResult?.missing_slots.map((slot, idx) => `${idx + 1}. ${slot}`).join('\n') || '未知';
            Modal.error({
                title: '无法归档',
                content: `报关单资料不齐全，缺少以下 ${checkResult?.missing_count || 0} 项文件：\n\n${missingFilesList}\n\n请先上传完整资料后再归档。`,
                width: 500,
                okText: '知道了'
            });
            return;
        }
    }
    
    // 其他状态变更需要确认
    const currentLabel = currentStatusConfig.value?.label || detail.value.status;
    Modal.confirm({
        title: `确认${description}？`,
        content: `当前状态：${currentLabel}，即将变更为：${description}`,
        async onOk() {
            await performStatusChange(newStatus);
        }
    });
}

// 确认修撤申请
async function handleAmendmentConfirm() {
    if (!amendmentReason.value.trim()) {
        message.error('请输入修撤原因');
        return;
    }
    
    if (pendingStatusChange.value) {
        amendmentModalVisible.value = false;
        await performStatusChange(pendingStatusChange.value.status, amendmentReason.value);
        pendingStatusChange.value = null;
    }
}

// 取消修撤申请
function handleAmendmentCancel() {
    amendmentModalVisible.value = false;
    amendmentReason.value = '';
    pendingStatusChange.value = null;
}


// 执行状态变更
async function performStatusChange(newStatus: string, reason?: string) {
    if (!id.value) return;
    try {
        statusChanging.value = true;
        await changeDeclarationStatusApi(Number(id.value), newStatus, reason);
        message.success('状态变更成功');
        await loadData();
        await loadAllowedTransitions();
    } catch (e: any) {
        console.error(e);
        message.error(e.message || '状态变更失败');
    } finally {
        statusChanging.value = false;
    }
}

// 检查文件完整性
async function checkFilesComplete() {
    if (!detail.value) return null;
    
    filesChecking.value = true;
    try {
        const result = await checkFilesCompleteApi(detail.value.id);
        filesCheckResult.value = result;
        return result;
    } catch (error) {
        console.error('检查文件完整性失败:', error);
        return null;
    } finally {
        filesChecking.value = false;
    }
}

// 打开下载选择弹窗
function handleDownload() {
    downloadModalVisible.value = true;
}

// 全选/取消全选
const isAllSelected = computed(() => {
    return selectedDownloadItems.value.length === downloadOptions.length;
});

const isIndeterminate = computed(() => {
    const len = selectedDownloadItems.value.length;
    return len > 0 && len < downloadOptions.length;
});

function handleSelectAll(checked: boolean) {
    if (checked) {
        selectedDownloadItems.value = downloadOptions.map(opt => opt.value);
    } else {
        selectedDownloadItems.value = [];
    }
}

// 下载归档资料（独立功能，仅在已归档状态时可用）
async function handleDownloadArchivedFiles() {
    if (!detail.value) return;
    
    try {
        downloadLoading.value = true;
        
        const response = await downloadDeclarationPdfApi(detail.value.id, ['files']);
        const { pdf_base64, filename } = response;
        
        // Base64 解码并下载
        const binaryString = atob(pdf_base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        
        // 触发下载
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `归档资料_${detail.value.pre_entry_no}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        message.success('归档资料下载成功');
    } catch (error: any) {
        console.error('下载归档资料失败:', error);
        message.error(error.message || '归档资料下载失败，请稍后重试');
    } finally {
        downloadLoading.value = false;
    }
}

// 确认下载
async function handleConfirmDownload() {
    if (selectedDownloadItems.value.length === 0) {
        message.warning('请至少选择一项资料');
        return;
    }
    
    try {
        downloadLoading.value = true;
        
        if (downloadMode.value === 'merged') {
            // 合并下载模式 - 生成一个PDF
            message.loading({ content: '正在生成合并PDF...', key: 'download', duration: 0 });
            await downloadMergedPdf();
        } else {
            // 分别下载模式 - 生成多个PDF
            message.loading({ content: `正在生成 ${selectedDownloadItems.value.length} 个PDF文件...`, key: 'download', duration: 0 });
            await downloadSeparatePdfs();
        }
        
        message.success({ content: 'PDF下载成功！', key: 'download' });
        downloadModalVisible.value = false;
        
    } catch (e: any) {
        console.error(e);
        message.error({ content: e.message || '下载失败', key: 'download' });
    } finally {
        downloadLoading.value = false;
    }
}

// 合并下载PDF
async function downloadMergedPdf() {
    const res = await downloadDeclarationPdfApi(Number(id.value), selectedDownloadItems.value);
    downloadPdfFromBase64(res.pdf_base64, res.filename);
}

// 分别下载多个PDF
async function downloadSeparatePdfs() {
    const docTypeNames: Record<string, string> = {
        'declaration': '报关单',
        'packing': '装箱单',
        'invoice': '发票',
        'contract': '合同',
        'proxy': '委托书',
        'files': '归档资料'
    };
    
    for (const item of selectedDownloadItems.value) {
        // 为每个文档类型单独调用API
        const res = await downloadDeclarationPdfApi(Number(id.value), [item]);
        
        // 修改文件名，添加文档类型标识
        const typeName = docTypeNames[item] || item;
        const filename = res.filename.replace('.pdf', `_${typeName}.pdf`);
        
        downloadPdfFromBase64(res.pdf_base64, filename);
        
        // 添加延迟，避免浏览器同时下载多个文件被阻止
        await new Promise(resolve => setTimeout(resolve, 300));
    }
}

// 从Base64下载PDF
function downloadPdfFromBase64(base64: string, filename: string) {
    // Base64解码为二进制数据
    const binaryString = window.atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    
    // 创建Blob并下载
    const blob = new Blob([bytes], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `${detail.value.pre_entry_no || 'declaration'}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// 取消下载
function handleCancelDownload() {
    downloadModalVisible.value = false;
}

// 引入配置
const {
  declarationFormItems,
  productColumns,
  packingInfoConfig,
  packingListColumns,
  invoiceColumns,
  contractInfoConfig,
  proxyInfoConfig
} = useDeclarationConfig(detail);

onMounted(() => {
  loadData();
  loadDictionaries();
  loadAllowedTransitions();
});
</script>

<template>
  <Page
    :title="pageTitle"
    content-class="p-6 space-y-4"
  >
    <!-- Header Extra Buttons -->
    <template #extra>
       <Space>
        <!-- 查看模式 -->
        <template v-if="!isEditMode">
            <!-- 状态操作按钮 -->
            <Dropdown v-if="allowedTransitions && allowedTransitions.allowed_transitions.length > 0" :trigger="['click']">
                <Button type="primary" :loading="statusChanging">
                    <SendOutlined /> 状态操作
                </Button>
                <template #overlay>
                    <Menu>
                        <Menu.Item 
                            v-for="trans in allowedTransitions.allowed_transitions" 
                            :key="trans.status"
                            @click="handleStatusChange(trans.status, trans.description)"
                        >
                            {{ trans.description }}
                        </Menu.Item>
                    </Menu>
                </template>
            </Dropdown>
            
            <Button type="primary" @click="handleDownload">
                <DownloadOutlined /> 下载资料
            </Button>
            
            <!-- 下载归档资料按钮（已归档状态时高亮可用，其他状态禁用） -->
            <Button 
                @click="handleDownloadArchivedFiles"
                :type="detail?.status === 'archived' ? 'primary' : 'default'"
                :disabled="detail?.status !== 'archived'"
                :loading="downloadLoading"
            >
                <FileOutlined /> 下载归档资料
            </Button>
            
            <!-- 文件不齐全警告（仅在已放行且文件不齐全时显示） -->
            <div 
                v-if="detail?.status === 'cleared' && filesCheckResult && !filesCheckResult.is_complete"
                class="flex items-center px-3 py-2 bg-yellow-50 border border-yellow-200 rounded"
            >
                <WarningOutlined class="text-yellow-600 mr-2" />
                <span class="text-sm text-yellow-800">
                    资料不齐全（缺 {{ filesCheckResult.missing_count }} 项）
                </span>
            </div>
            
            <Button v-if="!allowedTransitions?.is_locked" @click="handleEnterEdit">
                <EditOutlined /> 编辑
            </Button>
        </template>

        <!-- 编辑模式 -->
        <template v-else>
            <Button @click="handleCancel">
                 <CloseOutlined /> 取消
            </Button>
            <Button type="primary" :loading="submitting" @click="handleSave">
                <SaveOutlined /> 保存
            </Button>
        </template>
       </Space>
    </template>
    
    <!-- 状态流程条 -->
    <section class="bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border rounded-lg px-6 py-3 mb-4">
          <!-- 异常状态提示 -->
        <div v-if="isExceptionStatus" class="flex items-center gap-3 p-3 rounded-lg border" :class="[currentStatusConfig?.bgColor, 'border-current']">
                  <component :is="currentStatusConfig?.icon" :class="[currentStatusConfig?.color, 'text-2xl']" />
            <div class="flex-1">
                <p class="font-semibold" :class="currentStatusConfig?.color">{{ currentStatusConfig?.label }}</p>
                <p class="text-xs text-muted-foreground mt-0.5">
                    {{ detail.marks_and_notes || '流程异常，请关注状态变更' }}
                </p>
                      </div>
            <Tag v-if="allowedTransitions?.is_locked" color="red">已锁定</Tag>
          </div>

        <!-- 标准流程条 -->
        <div v-else class="flex flex-wrap gap-2 items-center">
              <template v-for="(step, index) in statusFlow" :key="step.value">
                  <div 
                      class="px-3 py-2 rounded border transition-all flex items-center gap-2"
                      :class="[
                          index <= currentStepIndex
                              ? `${step.color} ${step.bgColor} border-current font-semibold`
                              : 'border-gray-200 dark:border-gray-700 text-gray-400',
                          index === currentStepIndex ? 'ring-2 ring-offset-1 ring-current' : ''
                      ]"
                  >
                      <component :is="step.icon" class="text-base" />
                      <span class="text-xs font-bold">{{ step.label }}</span>
                      <span v-if="index < currentStepIndex" class="text-green-500 text-xs">✓</span>
                      <span 
                          v-if="index === currentStepIndex" 
                          class="inline-block w-1.5 h-1.5 rounded-full animate-pulse"
                          :class="step.bgColor"
                      />
                  </div>
                  <RightOutlined 
                      v-if="index < statusFlow.length - 1" 
                      class="text-xs"
                      :class="index < currentStepIndex ? 'text-green-500' : 'text-gray-300 dark:text-gray-600'"
                  />
              </template>
          </div>
    </section>
      
    <!-- 基本信息区域 -->
    <Card :bordered="false">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4 text-sm">
            <!-- Col 1: 报关单配置 -->
            <dl class="space-y-3">
                <div class="flex items-start gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">报关单类型</dt>
                    <dd class="flex flex-wrap gap-x-2 font-medium">
                        <span v-for="type in docTypes" :key="type">{{ type }}</span>
                    </dd>
                  </div>
                <div class="flex items-center gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">货柜模式</dt>
                    <dd v-if="!isEditMode">
                        <Tag v-if="detail.container_mode === 'FCL'" color="blue">整柜 (FCL)</Tag>
                        <Tag v-else-if="detail.container_mode === 'LCL'" color="orange">散货 (LCL)</Tag>
                        <span v-else class="text-muted-foreground">-</span>
                    </dd>
                    <dd v-else>
                  <Select 
                      v-model:value="detail.container_mode"
                      size="small"
                      class="w-32"
                      :options="[
                          { label: '整柜 (FCL)', value: 'FCL' },
                          { label: '散货 (LCL)', value: 'LCL' }
                      ]"
                  />
                    </dd>
              </div>
                <div class="flex items-center gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">附件</dt>
                    <dd>
                      <Button v-if="isEditMode" type="link" size="small" class="p-0 h-auto">
                         <PaperClipOutlined /> 上传附件
                      </Button>
                        <span v-else class="text-muted-foreground text-xs">点击编辑后可上传</span>
                    </dd>
              </div>
            </dl>

            <!-- Col 2: 交易主体 -->
            <dl class="space-y-3">
                <div class="flex items-center gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">成交币种</dt>
                    <dd v-if="!isEditMode" class="font-medium">{{ detail.currency || 'USD' }}</dd>
                    <dd v-else>
                  <Select 
                      v-model:value="detail.currency"
                      size="small"
                      class="w-32"
                      show-search
                      :options="currencyOptions"
                  />
                    </dd>
              </div>
                <div class="flex items-center gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">境内发货人</dt>
                    <dd v-if="!isEditMode">{{ detail.internal_shipper_name || '未设置' }}</dd>
                    <dd v-else>
                  <Select
                      v-model:value="detail.internal_shipper_id"
                      size="small"
                      class="w-64"
                      show-search
                      option-filter-prop="label"
                      :options="companyOptions.map(c => ({ label: c.legal_name, value: c.id }))"
                      placeholder="请选择境内发货人"
                  />
                    </dd>
              </div>
                <div class="flex items-center gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">境外收货人</dt>
                    <dd v-if="!isEditMode" class="truncate" :title="detail.overseas_consignee">
                        {{ detail.overseas_consignee || '-' }}
                    </dd>
                    <dd v-else>
                  <Select 
                      v-model:value="detail.overseas_consignee" 
                      size="small" 
                      class="w-64"
                      show-search
                      :options="consigneeOptions.map(c => ({ label: c.name, value: c.name }))"
                      placeholder="请选择或输入"
                  />
                    </dd>
              </div>
            </dl>

            <!-- Col 3: 单据编号 -->
            <dl class="space-y-3">
                <div class="flex items-center gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">预录入号</dt>
                    <dd class="font-mono text-primary font-semibold">{{ detail.pre_entry_no || '-' }}</dd>
              </div>
                <div class="flex items-center gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">报关单号</dt>
                    <dd class="font-mono font-medium">{{ detail.customs_no || '-' }}</dd>
              </div>
                <div class="flex items-center gap-3">
                    <dt class="text-muted-foreground w-20 shrink-0">关联单据</dt>
                    <dd>
                        <Button type="link" size="small" class="p-0 h-auto">
                      {{ detail.pre_entry_no ? 'OWS-' + detail.pre_entry_no : '-' }} <LinkOutlined />
                  </Button>
                    </dd>
              </div>
            </dl>
        </div>
      </Card>

    <!-- 主内容区 - Tabs -->
    <Card :bordered="false">
        <Tabs v-model:activeKey="activeTab" type="card">
            <Tabs.TabPane key="declaration" tab="报关单">
                <DeclarationTab 
                    :detail="detail"
                    :is-edit-mode="isEditMode"
                    :form-items="declarationFormItems"
                    :columns="productColumns"
                    :country-options="countryOptions"
                    :port-options="portOptions"
                    :transaction-mode-options="transactionModeOptions"
                    :trade-mode-options="tradeModeOptions"
                    :nature-of-exemption-options="natureOfExemptionOptions"
                    :transport-mode-options="transportModeOptions"
                    :company-options="companyOptions"
                    :calculate-fob-unit-price="calculateFobUnitPrice"
                />
            </Tabs.TabPane>

            <Tabs.TabPane key="packing" tab="装箱单">
                <PackingTab 
                    :detail="detail"
                    :info-config="packingInfoConfig"
                    :columns="packingListColumns"
                    :is-edit-mode="isEditMode"
                />
            </Tabs.TabPane>
            
            <Tabs.TabPane key="invoice" tab="发票">
                <InvoiceTab 
                    :detail="detail"
                    :columns="invoiceColumns"
                    :is-edit-mode="isEditMode"
                    :transaction-mode-options="transactionModeOptions"
                    :consignee-options="consigneeOptions.map(c => ({ label: c.name, value: c.name }))"
                />
            </Tabs.TabPane>

            <Tabs.TabPane key="contract" tab="合同">
                <ContractTab 
                    :detail="detail"
                    :info-config="contractInfoConfig"
                    :columns="invoiceColumns"
                    :is-edit-mode="isEditMode"
                    :transaction-mode-options="transactionModeOptions"
                    :consignee-options="consigneeOptions.map(c => ({ label: c.name, value: c.name }))"
                />
            </Tabs.TabPane>
            
            <Tabs.TabPane key="proxy" tab="委托书">
                <ProxyTab 
                    :detail="detail"
                    :info-config="proxyInfoConfig"
                    :columns="invoiceColumns"
                    :is-edit-mode="isEditMode"
                />
            </Tabs.TabPane>

            <Tabs.TabPane key="files" tab="归档资料">
                <DeclarationFilePanel 
                    :declarationId="Number(id)" 
                    :initial-files="fileList"
                    :required-slots="detail.required_file_slots"
                    :readonly="!isEditMode"
                />
            </Tabs.TabPane>
        </Tabs>
    </Card>

    <!-- 修撤原因输入 Modal -->
    <Modal
        v-model:open="amendmentModalVisible"
        title="申请修撤"
        :confirmLoading="statusChanging"
        @ok="handleAmendmentConfirm"
        @cancel="handleAmendmentCancel"
    >
            <p class="mb-2 text-sm text-muted-foreground">请详细说明修撤原因：</p>
            <Textarea
                v-model:value="amendmentReason"
                :rows="4"
                placeholder="请输入修撤原因..."
                :maxlength="500"
                show-count
            />
    </Modal>

    <!-- 下载选择 Modal -->
    <Modal
        v-model:open="downloadModalVisible"
        title="选择下载内容"
        width="600px"
        :confirmLoading="downloadLoading"
        @ok="handleConfirmDownload"
        @cancel="handleCancelDownload"
    >
        <div class="space-y-4">
            <!-- 下载模式选择 -->
            <div class="pb-3 border-b">
                <div class="font-semibold mb-2">下载模式</div>
                <Radio.Group v-model:value="downloadMode" class="w-full">
                    <Radio value="merged" class="block mb-2">
                        <div class="ml-2">
                            <div class="font-medium">合并下载</div>
                            <div class="text-xs text-muted-foreground">所有选中的文档合并为一个PDF文件</div>
                        </div>
                    </Radio>
                    <Radio value="separate" class="block">
                        <div class="ml-2">
                            <div class="font-medium">分别下载</div>
                            <div class="text-xs text-muted-foreground">每个文档类型生成单独的PDF文件</div>
                        </div>
                    </Radio>
                </Radio.Group>
            </div>
            
            <!-- 全选控制 -->
            <div class="pb-3 border-b">
                <Checkbox
                    :checked="isAllSelected"
                    :indeterminate="isIndeterminate"
                    @change="(e: any) => handleSelectAll(e.target.checked)"
                >
                    <span class="font-semibold">全选</span>
                    <span class="text-xs text-muted-foreground ml-2">
                        (已选 {{ selectedDownloadItems.length }}/{{ downloadOptions.length }} 项)
                    </span>
                </Checkbox>
            </div>

            <!-- 选项列表 -->
            <Checkbox.Group v-model:value="selectedDownloadItems" class="w-full">
                <div class="space-y-3">
                    <div
                        v-for="option in downloadOptions"
                        :key="option.value"
                        class="flex items-start p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-all cursor-pointer"
                    >
                        <Checkbox :value="option.value" class="mt-0.5">
                            <div class="ml-2">
                                <div class="font-medium text-foreground">{{ option.label }}</div>
                                <div class="text-xs text-muted-foreground mt-1">{{ option.description }}</div>
                            </div>
                        </Checkbox>
                    </div>
                </div>
            </Checkbox.Group>

            <!-- 说明信息 -->
            <div class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <p class="text-xs text-blue-600 dark:text-blue-400">
                    <strong>📄 下载说明：</strong><br />
                    • 将生成包含所选内容的PDF文件<br />
                    • 归档资料将以附件清单形式展示<br />
                    • 下载的PDF文件名为：{{ detail.pre_entry_no || '报关单' }}.pdf
                </p>
            </div>
        </div>
    </Modal>
  </Page>
</template>
