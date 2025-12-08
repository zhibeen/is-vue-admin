<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';
import { Card, Table, Button, Modal, Form, Input, Switch, message, Space, Tag, Row, Col, InputNumber, Divider, Popconfirm, Alert, Select, Tooltip, Drawer, Radio, type SelectProps } from 'ant-design-vue';
import { PlusOutlined, ReloadOutlined, InfoCircleOutlined, SettingOutlined, DatabaseOutlined, LockOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { getDictsApi, getDictItemsApi, createDictApi, updateDictApi, deleteDictApi } from '#/api/system/dict';
import type { Dict, DictItem } from '#/api/system/dict';

// --- Configuration: Usage Help ---
// 定义不同字典类型的配置说明
const dictUsageConfig: Record<string, { title: string; description: string; example: string }> = {
    'product_business_type': {
        title: '产品业务类型配置',
        description: '配置产品业务类型相关的策略，例如是否需要额外的验证流程。',
        example: JSON.stringify({
            "strategy": "vehicle",
            "requires_audit": true,
            "max_daily_limit": 1000
        }, null, 2)
    },
    'system_role_type': {
        title: '系统角色类型',
        description: '定义系统角色的默认权限等级。',
        example: JSON.stringify({
            "default_level": 1,
            "allow_custom_permissions": false
        }, null, 2)
    }
};

const defaultUsageConfig = {
    title: '通用配置说明',
    description: '使用 JSON 格式配置该字典项的额外属性。',
    example: JSON.stringify({
        "key": "value",
        "config": true
    }, null, 2)
};

// 计算当前选中的配置说明
const currentUsage = computed(() => {
    if (!selectedDict.value) return null;
    return dictUsageConfig[selectedDict.value.code] || defaultUsageConfig;
});

// 计算预设值选项
const dictValueOptions = computed(() => {
    if (selectedDict.value?.value_options && Array.isArray(selectedDict.value.value_options) && selectedDict.value.value_options.length > 0) {
        return selectedDict.value.value_options.map((opt: any) => ({
             label: `${opt.label} (${opt.value})`,
             value: opt.value,
             originLabel: opt.label
        }));
    }
    return [];
});

// 判断当前选中的字典是否为配置型 (JSON) 模式
const isConfigMode = computed(() => {
    return selectedDict.value && Array.isArray(selectedDict.value.value_options) && selectedDict.value.value_options.length > 0;
});

// 当选择预设值时，自动填充 Label
const handleDictValueChange: SelectProps['onChange'] = (val) => {
    const opt = dictValueOptions.value.find(o => o.value === val);
    if (opt) {
        itemFormState.value.label = opt.originLabel;
    }
};

// --- State: Dicts (Left) ---
const dicts = ref<Dict[]>([]);
const loadingDicts = ref(false);
const selectedDict = ref<Dict | null>(null);

// --- State: Items (Right) ---
const items = ref<DictItem[]>([]);
const loadingItems = ref(false);

// --- Modals ---
const dictModalVisible = ref(false);
const dictFormRef = ref();
const dictFormState = ref({
    id: '',
    code: '',
    name: '',
    category: undefined,
    description: '',
    is_system: false,
    value_options_str: '[]'
});
const isEditDict = ref(false);

// --- Filter State ---
const activeCategory = ref('all');
const searchText = ref('');

// 动态计算分类选项
const categoryOptions = computed(() => {
    // 1. 基础选项
    const options = [
        { label: $t('sys.dict.category.all'), value: 'all' }
    ];
    
    // 2. 收集所有已存在的分类 (包括后端返回的数据)
    // 预定义常用分类 Key，用于控制排序顺序
    const predefinedKeys = ['product', 'purchase', 'supply', 'finance', 'system'];
    const existingCategories = new Set(predefinedKeys);
    
    // 从当前字典数据中提取分类
    if (dicts.value) {
        dicts.value.forEach(d => {
            if (d.category) {
                existingCategories.add(d.category);
            }
        });
    }
    
    // 3. 生成选项列表
    // 优先显示预定义的顺序，然后是其他自定义分类
    const sortedCats = Array.from(existingCategories).sort((a, b) => {
        const idxA = predefinedKeys.indexOf(a);
        const idxB = predefinedKeys.indexOf(b);
        
        // 都在预定义列表中，按预定义顺序
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        // A 在预定义中，B 不在，A 排前
        if (idxA !== -1) return -1;
        // B 在预定义中，A 不在，B 排前
        if (idxB !== -1) return 1;
        
        // 都不在，按字母顺序
        return a.localeCompare(b);
    });

    sortedCats.forEach(cat => {
        // 尝试翻译，Key 格式为 sys.dict.category.{cat}
        // 利用 i18n 的回退机制，如果 key 不存在通常会返回 key 本身
        // 为了更稳健，我们手动判断一下
        const key = `sys.dict.category.${cat}`;
        const translated = $t(key);
        
        // 简单的启发式判断：如果翻译结果等于 Key 本身，说明没翻译，显示原始 Code
        // 注意：Vben 的 $t 可能直接返回 Key 字符串，也可能配置为返回空，视配置而定
        // 这里假设如果翻译后包含 'sys.dict' 字样则表示未找到翻译
        const label = translated.includes('sys.dict.category') ? cat : translated;

        options.push({
            label: label,
            value: cat
        });
    });

    return options;
});

// 过滤后的字典列表
const filteredDicts = computed(() => {
    let res = dicts.value;
    
    // 1. Category Filter
    if (activeCategory.value !== 'all') {
        res = res.filter(d => d.category === activeCategory.value);
    }
    
    // 2. Search Filter
    if (searchText.value) {
        const key = searchText.value.toLowerCase().trim();
        res = res.filter(d => 
            d.name.toLowerCase().includes(key) || 
            d.code.toLowerCase().includes(key)
        );
    }
    
    return res;
});

// --- Columns ---
const dictColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '操作', key: 'action', width: 60, align: 'center' as const },
];

const itemColumns = [
    { title: '标签', dataIndex: 'label', key: 'label' },
    { title: '键值', dataIndex: 'value', key: 'value' },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 80 },
    { title: '状态', key: 'status', width: 80 },
    { title: '配置 (Meta)', key: 'meta', ellipsis: true },
];

// --- Lifecycle ---
onMounted(() => {
    loadDicts();
});

// --- Logic: Dicts ---
async function loadDicts() {
    loadingDicts.value = true;
    try {
        dicts.value = await getDictsApi();
        if (!selectedDict.value && dicts.value.length > 0) {
            handleSelectDict(dicts.value[0] as Dict);
        }
    } catch (e) {
        message.error('加载字典列表失败');
    } finally {
        loadingDicts.value = false;
    }
}

function handleSelectDict(record: Dict) {
    // 兼容可能为 null 的 value_options
    const recordWithDefaults: Dict = {
        ...record,
        value_options: record.value_options || [],
    };
    selectedDict.value = recordWithDefaults;
    loadItems();
}

function handleAddDict() {
    isEditDict.value = false;
    dictFormState.value = { 
        id: '', 
        code: '', 
        name: '', 
        category: undefined, 
        description: '', 
        is_system: false, 
        value_options_str: '[]' 
    };
    dictModalVisible.value = true;
}

function handleEditDict(record: Dict) {
    isEditDict.value = true;
    dictFormState.value = { 
        id: record.id,
        code: record.code,
        name: record.name,
        category: record.category as any,
        description: record.description || '',
        is_system: record.is_system,
        value_options_str: JSON.stringify(record.value_options || [], null, 2)
    };
    dictModalVisible.value = true;
}

async function handleSaveDict() {
    try {
        await dictFormRef.value.validate();
        
        let valueOptions = [];
        
        try {
            valueOptions = JSON.parse(dictFormState.value.value_options_str);
            if (!Array.isArray(valueOptions)) throw new Error();
        } catch (e) {
            message.error('预设值选项必须是 JSON 数组');
            return;
        }
        
        const payload = {
            ...dictFormState.value,
            value_options: valueOptions
        };
        
        // Remove helper fields
        delete (payload as any).value_options_str;
        
        if (payload.is_system) delete (payload as any).is_system;
        if (payload.id) delete (payload as any).id;
        
        if (isEditDict.value) {
            await updateDictApi(dictFormState.value.id, payload);
            message.success('更新成功');
        } else {
            const res = await createDictApi(payload);
            message.success('创建成功');
            // 如果创建的是新字典，尝试选中它
            if (res && res.id) {
                // 重新加载列表后可能会选中第一个，这里逻辑可以优化
            }
        }
        dictModalVisible.value = false;
        loadDicts();
    } catch (e) {
        console.error(e);
    }
}

async function handleDeleteDict(id: string) {
    try {
        await deleteDictApi(id);
        message.success('删除成功');
        selectedDict.value = null;
        loadDicts();
    } catch (e) {
        console.error(e);
    }
}

// --- Logic: Items ---
async function loadItems() {
    if (!selectedDict.value) return;
    loadingItems.value = true;
    try {
        items.value = await getDictItemsApi(selectedDict.value.code);
    } catch (e) {
        message.error('加载字典项失败');
    } finally {
        loadingItems.value = false;
    }
}

</script>

<template>
    <Page title="系统字典管理">
        <div class="p-4 h-full flex gap-4">
            <!-- Left: Dict List with Side Navigation -->
            <Card class="w-2/5 flex flex-col" :bodyStyle="{ padding: 0, flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'row' }">
                
                <!-- 1. Side Category Nav -->
                <div class="w-24 bg-gray-50 border-r flex flex-col h-full pt-2">
                    <div 
                        v-for="opt in categoryOptions" 
                        :key="opt.value"
                        class="px-2 py-3 text-center cursor-pointer hover:text-blue-600 text-xs transition-colors relative"
                        :class="activeCategory === opt.value ? 'text-blue-600 font-bold bg-white' : 'text-gray-600'"
                        @click="activeCategory = opt.value"
                    >
                        {{ opt.label }}
                        <!-- Active Indicator -->
                        <div v-if="activeCategory === opt.value" class="absolute left-0 top-0 bottom-0 w-1 bg-blue-600"></div>
                    </div>
                </div>

                <!-- 2. Dict List -->
                <div class="flex-1 flex flex-col h-full p-3 overflow-hidden">
                    <div class="mb-3 flex-shrink-0">
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-bold text-base">字典列表</span>
                            <Space :size="4">
                                <Button type="text" size="small" @click="loadDicts">
                                    <template #icon><ReloadOutlined /></template>
                                </Button>
                                <Button type="primary" size="small" @click="handleAddDict">
                                    <template #icon><PlusOutlined /></template>
                                </Button>
                            </Space>
                        </div>
                        
                        <!-- Search Box -->
                        <Input.Search 
                            v-model:value="searchText" 
                            placeholder="搜索..." 
                            size="small" 
                            allow-clear 
                        />
                    </div>
                    
                    <Table
                        :columns="dictColumns"
                        :data-source="filteredDicts"
                        :loading="loadingDicts"
                        row-key="id"
                        size="small"
                        :pagination="false"
                        :scroll="{ y: 'calc(100vh - 220px)' }"
                        :row-class-name="(record) => record.id === selectedDict?.id ? 'bg-blue-50 cursor-pointer' : 'cursor-pointer hover:bg-gray-50'"
                        :custom-row="(record: Dict) => ({
                            onClick: () => handleSelectDict(record)
                        })"
                    >
                        <template #bodyCell="{ column, record }">
                            <template v-if="column.key === 'name'">
                                <div class="flex items-center">
                                    <Tooltip v-if="record.value_options && record.value_options.length > 0" title="配置型 (JSON)">
                                        <SettingOutlined class="text-blue-500 mr-2" />
                                    </Tooltip>
                                    <Tooltip v-else title="数据型 (Table)">
                                        <DatabaseOutlined class="text-gray-400 mr-2" />
                                    </Tooltip>
                                    <div class="flex flex-col overflow-hidden">
                                        <span class="truncate font-medium">{{ record.name }}</span>
                                        <span class="text-xs text-gray-400 truncate">{{ record.code }}</span>
                                    </div>
                                </div>
                            </template>
                            <template v-if="column.key === 'action'">
                                <Space :size="0">
                                    <Button type="link" size="small" @click.stop="handleEditDict(record as Dict)">
                                        <EditOutlined />
                                    </Button>
                                    <Popconfirm title="删除?" @confirm.stop="handleDeleteDict((record as Dict).id)">
                                        <Button type="link" danger size="small">
                                            <template #icon><DeleteOutlined /></template>
                                        </Button>
                                    </Popconfirm>
                                </Space>
                            </template>
                        </template>
                    </Table>
                </div>
            </Card>

            <!-- Right: Items List -->
            <Card class="flex-1 flex flex-col" :bodyStyle="{ padding: '12px', flex: 1, overflow: 'hidden' }">
                <div v-if="!selectedDict" class="flex items-center justify-center h-full text-gray-400">
                    请选择左侧字典查看详情
                </div>
                <div v-else class="flex flex-col h-full">
                    <div class="mb-4 flex justify-between items-center border-b pb-2">
                        <div>
                            <Space>
                                <span class="font-bold text-lg mr-2">{{ selectedDict.name }}</span>
                                <Tag color="blue">配置型</Tag>
                            </Space>
                            <div class="mt-1">
                                <Tag class="font-mono">{{ selectedDict.code }}</Tag>
                                <span class="text-gray-400 text-sm ml-2">{{ selectedDict.description }}</span>
                            </div>
                        </div>
                        <Space>
                            <Button type="text" size="small" @click="loadItems">
                                <template #icon><ReloadOutlined /></template>
                            </Button>
                            
                            <!-- Show Edit Config Button -->
                            <Button type="primary" ghost size="small" @click="handleEditDict(selectedDict)">
                                <template #icon><EditOutlined /></template> 调整配置
                            </Button>
                        </Space>
                    </div>

                    <Alert type="info" show-icon class="mb-4">
                        <template #message>此字典由 JSON 配置托管</template>
                        <template #description>
                            条目数据源于字典配置。如需修改，请点击右上角"调整配置"。
                        </template>
                    </Alert>

                    <Alert v-if="currentUsage && currentUsage !== defaultUsageConfig" type="warning" show-icon class="mb-4" closable>
                        <template #message>业务配置说明：{{ currentUsage.title }}</template>
                        <template #description>
                            <span class="text-xs">{{ currentUsage.description }}</span>
                        </template>
                    </Alert>

                    <Table
                        :columns="itemColumns"
                        :data-source="items"
                        :loading="loadingItems"
                        row-key="id"
                        size="middle"
                        :pagination="false"
                        :scroll="{ y: 'calc(100vh - 350px)' }"
                    >
                        <template #bodyCell="{ column, record }">
                            <template v-if="column.key === 'value'">
                                <Tag color="blue">{{ (record as DictItem).value }}</Tag>
                            </template>
                            <template v-if="column.key === 'status'">
                                <Switch size="small" :checked="(record as DictItem).is_active" disabled />
                            </template>
                            <template v-if="column.key === 'meta'">
                                <span class="text-xs text-gray-500 font-mono" v-if="(record as DictItem).meta_data">
                                    {{ JSON.stringify((record as DictItem).meta_data) }}
                                </span>
                            </template>
                        </template>
                    </Table>
                </div>
            </Card>
        </div>

        <!-- Dict Modal -->
        <Modal v-model:open="dictModalVisible" :title="isEditDict ? '编辑字典' : '新增字典'" @ok="handleSaveDict">
            <Form ref="dictFormRef" :model="dictFormState" layout="vertical" class="pt-4">
                <Form.Item label="字典名称" name="name" :rules="[{ required: true }]">
                    <Input v-model:value="dictFormState.name" placeholder="例如：产品业务类型" />
                </Form.Item>
                <Form.Item label="业务分类" name="category">
                    <Select 
                        v-model:value="dictFormState.category" 
                        placeholder="请选择或输入业务分类" 
                        allow-clear
                        show-search
                    >
                        <Select.Option 
                            v-for="opt in categoryOptions.filter(o => o.value !== 'all')" 
                            :key="opt.value" 
                            :value="opt.value"
                        >
                            {{ opt.label }} ({{ opt.value }})
                        </Select.Option>
                    </Select>
                </Form.Item>
                <Form.Item label="字典编码" name="code" :rules="[{ required: true }]">
                    <Input v-model:value="dictFormState.code" :disabled="isEditDict" placeholder="例如：product_business_type" />
                </Form.Item>
                <Form.Item label="描述" name="description">
                    <Input.TextArea v-model:value="dictFormState.description" />
                </Form.Item>
                
                <div class="bg-blue-50 p-3 rounded mb-4 border border-blue-100">
                    <div class="text-xs text-blue-600 mb-2">
                        <InfoCircleOutlined /> 字典项配置。数据直接存储在字典定义中。
                    </div>
                    <Form.Item label="预设值选项 (JSON)" name="value_options_str" :noStyle="true">
                         <Input.TextArea v-model:value="dictFormState.value_options_str" :auto-size="{ minRows: 6, maxRows: 12 }" class="font-mono text-sm" placeholder='[{"label": "选项A", "value": "a"}]' />
                    </Form.Item>
                </div>

            </Form>
        </Modal>
    </Page>
</template>

