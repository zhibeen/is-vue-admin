<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import { Page } from '@vben/common-ui';
import { Card, Table, Button, Modal, Form, Input, Select, message, Space, Tag, Popconfirm, Typography, Switch } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined, AppstoreOutlined, SearchOutlined } from '@ant-design/icons-vue';
import { getAttributeDefinitionsApi, createAttributeDefinitionApi, updateAttributeDefinitionApi, deleteAttributeDefinitionApi } from '#/api/core/product';
import { getDictItemsApi } from '#/api/core/product';
import type { CategoryAttribute } from '#/api/core/product';

const { Text } = Typography;

// --- State ---
const loading = ref(false);
const rawDataSource = ref<CategoryAttribute[]>([]); // 原始数据
const modalVisible = ref(false);
const modalTitle = ref('');
const isEditMode = ref(false);

// Filter State
const searchText = ref('');
const searchGroup = ref<string | undefined>(undefined);

// Dictionary state for groups
const groupOptions = ref<any[]>([]);
const originalGroupOptions = ref<any[]>([]);

const formRef = ref();
const formState = ref<Partial<CategoryAttribute>>({
  id: '',
  key: '',
  label: '',
  name_en: '',
  description: '',
  type: 'text',
  group_name: '',
  // is_global: true, // 假设所有在此管理的都是全局属性
  allow_custom: false,
  code_weight: 99,
  options: []
});

// Options editor state
const optionsEditorVisible = ref(false);
const editingOptions = ref<any[]>([]);
const newOptionItem = ref({ label: '', value: '' });

// --- Computed ---

// 前端过滤逻辑
const filteredDataSource = computed(() => {
  return rawDataSource.value.filter(item => {
    // 1. 关键词过滤 (名称、英文名、Key)
    const keyword = searchText.value.toLowerCase().trim();
    const matchKeyword = !keyword || 
      item.label.toLowerCase().includes(keyword) || 
      (item.name_en && item.name_en.toLowerCase().includes(keyword)) ||
      item.key.toLowerCase().includes(keyword);
      
    // 2. 分组过滤
    const matchGroup = !searchGroup.value || item.group_name === searchGroup.value;
    
    return matchKeyword && matchGroup;
  });
});

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60, align: 'center' as const },
  { title: '属性名称 (Label)', dataIndex: 'label', key: 'label', width: 150 },
  { title: '英文名称 (EN)', dataIndex: 'name_en', key: 'name_en', width: 150 }, 
  { title: '属性 Key', dataIndex: 'key', key: 'key', width: 180 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100, align: 'center' as const },
  { title: '分组', dataIndex: 'group_name', key: 'group_name', width: 120 },
  { title: '预设选项', dataIndex: 'options', key: 'options', ellipsis: true },
  { 
    title: '排序权重', 
    dataIndex: 'code_weight', 
    key: 'code_weight', 
    width: 100, 
    align: 'center' as const,
    sorter: (a: any, b: any) => (a.code_weight || 0) - (b.code_weight || 0)
  },
  { title: '操作', key: 'action', width: 180, fixed: 'right' as const, align: 'center' as const }
];

// --- Lifecycle ---

onMounted(() => {
  loadData();
  loadGroupDicts();
});

// --- Methods ---

async function loadGroupDicts() {
    try {
        const res = await getDictItemsApi('product_attribute_group');
        // getDictItemsApi returns DictItem[] directly or { data: DictItem[] }
        const items = Array.isArray(res) ? res : (res as any).data || [];
        
        groupOptions.value = items.map((item: any) => ({
            label: item.label,
            value: item.value
        }));
        originalGroupOptions.value = [...groupOptions.value];
    } catch (e) {
        console.error('Failed to load group dict', e);
    }
}

function handleGroupSearch(val: string) {
    if (!val) {
        groupOptions.value = [...originalGroupOptions.value];
        return;
    }
    const exists = originalGroupOptions.value.some(o => o.label === val || o.value === val);
    if (!exists) {
        groupOptions.value = [{ label: val, value: val }, ...originalGroupOptions.value];
    } else {
        groupOptions.value = [...originalGroupOptions.value];
    }
}

async function loadData() {
  loading.value = true;
  try {
    const res = await getAttributeDefinitionsApi();
    // 兼容 { data: [] } 和 [] 格式
    rawDataSource.value = (res as any).data || res;
  } catch (e) {
    message.error('加载失败');
  } finally {
    loading.value = false;
  }
}

function handleAdd() {
  isEditMode.value = false;
  modalTitle.value = '新增属性定义';
  formState.value = {
    key: '',
    label: '',
    name_en: '',
    description: '',
    type: 'text',
    group_name: '',
    code_weight: 99,
    options: []
  };
  modalVisible.value = true;
}

function handleEdit(record: CategoryAttribute) {
  isEditMode.value = true;
  modalTitle.value = '编辑属性定义';
  // 深度复制以避免直接修改表格数据
  formState.value = JSON.parse(JSON.stringify(record));
  modalVisible.value = true;
}

async function handleDelete(id: string) {
  try {
    await deleteAttributeDefinitionApi(id);
    message.success('删除成功');
    loadData();
  } catch (e) {
    message.error('删除失败，属性可能已被分类或商品使用');
  }
}

async function handleSave() {
  try {
    await formRef.value.validate();
    
    // 下拉类型校验
    if (formState.value.type === 'select' && (!formState.value.options || formState.value.options.length === 0)) {
        message.warning('“下拉选择”类型必须配置至少一个预设选项');
        return;
    }

    if (isEditMode.value) {
      await updateAttributeDefinitionApi(formState.value.id!, formState.value);
      message.success('更新成功');
    } else {
      await createAttributeDefinitionApi(formState.value);
      message.success('创建成功');
    }
    
    modalVisible.value = false;
    loadData();
  } catch (e) {
    console.error(e);
  }
}

// --- Options Logic ---
function openOptionsEditor() {
    const existing = formState.value.options || [];
    editingOptions.value = JSON.parse(JSON.stringify(existing));
    optionsEditorVisible.value = true;
}

function handleAddOption() {
    if (!newOptionItem.value.value) return;
    const val = newOptionItem.value.value;
    const label = newOptionItem.value.label || val;
    
    const exists = editingOptions.value.some((o: any) => {
        const v = typeof o === 'object' ? o.value : o;
        return v === val;
    });
    
    if (exists) {
        message.warning('选项值已存在');
        return;
    }
    
    editingOptions.value.push({ label, value: val });
    newOptionItem.value = { label: '', value: '' };
}

function handleRemoveOption(index: number) {
    editingOptions.value.splice(index, 1);
}

function removeFormOption(index: number) {
    if (formState.value.options) {
        formState.value.options.splice(index, 1);
    }
}

function handleSaveOptions() {
    formState.value.options = [...editingOptions.value];
    optionsEditorVisible.value = false;
}

function getTypeColor(type: string) {
    const map: Record<string, string> = {
        text: 'blue',
        number: 'cyan',
        boolean: 'purple',
        select: 'orange',
        textarea: 'geekblue'
    };
    return map[type] || 'default';
}
</script>

<template>
  <Page title="商品属性库管理">
    <div class="p-4">
      <Card :bordered="false" class="mb-4">
        <!-- 工具栏：搜索与操作 -->
        <div class="flex flex-col sm:flex-row justify-between gap-4 mb-4">
            <!-- 左侧：搜索筛选 -->
            <div class="flex flex-1 gap-2">
                <Input 
                    v-model:value="searchText" 
                    placeholder="搜索属性名称 / Key / 英文名" 
                    style="width: 240px" 
                    allow-clear
                >
                    <template #prefix><SearchOutlined class="text-gray-400" /></template>
                </Input>
                
                <Select
                    v-model:value="searchGroup"
                    placeholder="按分组筛选"
                    style="width: 160px"
                    allow-clear
                    :options="groupOptions"
                />
            </div>
            
            <!-- 右侧：按钮组 -->
            <Space>
                <Button type="primary" @click="handleAdd">
                    <PlusOutlined /> 新增属性
                </Button>
                <Button href="/system/dict" target="_blank">
                    <AppstoreOutlined /> 分组管理
                </Button>
            </Space>
        </div>
        
        <!-- 表格区域 -->
        <Table
          :columns="columns"
          :data-source="filteredDataSource"
          :loading="loading"
          row-key="id"
          size="middle"
          :pagination="{ 
            showSizeChanger: true, 
            showQuickJumper: true, 
            defaultPageSize: 20, 
            showTotal: (total) => `共 ${total} 条` 
          }"
        >
            <template #bodyCell="{ column, record }">
                <!-- 英文名称列：如果为空显示 - -->
                <template v-if="column.key === 'name_en'">
                    <span v-if="record.name_en">{{ record.name_en }}</span>
                    <span v-else class="text-gray-300">-</span>
                </template>

                <!-- Key 列：增加复制功能 -->
                <template v-if="column.key === 'key'">
                    <Text copyable>{{ record.key }}</Text>
                </template>

                <!-- 类型列 -->
                <template v-if="column.key === 'type'">
                    <Space direction="vertical" :size="2">
                        <Tag :color="getTypeColor(record.type)">{{ record.type }}</Tag>
                        <Tag v-if="record.type === 'select' && record.allow_custom" color="purple" class="text-xs scale-90 origin-left">可自定义</Tag>
                    </Space>
                </template>

                <!-- 分组列 -->
                <template v-if="column.key === 'group_name'">
                    <Tag v-if="record.group_name" color="blue">
                        {{ groupOptions.find((o: any) => o.value === record.group_name)?.label || record.group_name }}
                    </Tag>
                    <span v-else class="text-gray-400">默认</span>
                </template>

                <!-- 预设选项列 -->
                <template v-if="column.key === 'options'">
                    <template v-if="record.type === 'select'">
                        <div class="flex flex-wrap gap-1 max-h-[60px] overflow-hidden">
                            <Tag v-for="(opt, idx) in (record.options || []).slice(0, 3)" :key="idx" size="small" :bordered="false">
                                {{ typeof opt === 'object' ? opt.label : opt }}
                            </Tag>
                            <Tag v-if="(record.options || []).length > 3" size="small" class="bg-gray-100 text-gray-500">
                                +{{ (record.options || []).length - 3 }}
                            </Tag>
                        </div>
                    </template>
                    <span v-else class="text-gray-300">-</span>
                </template>

                <!-- 操作列 -->
                <template v-if="column.key === 'action'">
                    <Space>
                        <Button type="link" size="small" @click="handleEdit(record)">
                            <EditOutlined /> 编辑
                        </Button>
                        <Popconfirm title="确定要删除此属性吗？此操作不可恢复。" @confirm="handleDelete(record.id)">
                            <Button type="link" size="small" danger>
                                <DeleteOutlined /> 删除
                            </Button>
                        </Popconfirm>
                    </Space>
                </template>
            </template>
        </Table>
      </Card>

      <!-- 编辑/新增 弹窗 -->
      <Modal
        v-model:open="modalVisible"
        :title="modalTitle"
        @ok="handleSave"
        width="600px"
        :mask-closable="false"
      >
        <Form
            ref="formRef"
            :model="formState"
            layout="vertical"
            class="pt-4"
        >
            <div class="grid grid-cols-2 gap-4">
                <Form.Item 
                    label="属性名称 (Label)" 
                    name="label" 
                    :rules="[{ required: true, message: '请输入属性名称' }]"
                >
                    <Input v-model:value="formState.label" placeholder="如：额定电压" />
                </Form.Item>

                <Form.Item 
                    label="英文名称 (EN)" 
                    name="name_en" 
                    tooltip="用于生成英文报表或跨境业务显示"
                >
                    <Input v-model:value="formState.name_en" placeholder="如：Rated Voltage" />
                </Form.Item>
            </div>

            <Form.Item 
                label="属性 Key (Internal ID)" 
                name="key" 
                :rules="[
                    { required: true, message: '请输入唯一Key' },
                    { pattern: /^[a-z][a-z0-9_]*$/, message: 'Key 必须以小写字母开头，仅包含小写字母、数字和下划线' }
                ]"
                tooltip="系统内部唯一标识，一旦创建不建议修改"
            >
                <Input v-model:value="formState.key" placeholder="如：rated_voltage" :disabled="isEditMode">
                    <template #prefix v-if="!isEditMode"><span class="text-gray-400">attr_</span></template>
                </Input>
            </Form.Item>
            
            <div class="grid grid-cols-2 gap-4">
                <Form.Item label="数据类型" name="type">
                    <Select v-model:value="formState.type" :disabled="isEditMode">
                        <Select.Option value="text">单行文本 (Text)</Select.Option>
                        <Select.Option value="textarea">多行文本 (Textarea)</Select.Option>
                        <Select.Option value="number">数字 (Number)</Select.Option>
                        <Select.Option value="boolean">布尔开关 (Boolean)</Select.Option>
                        <Select.Option value="select">下拉单选 (Select)</Select.Option>
                    </Select>
                </Form.Item>

                <Form.Item label="所属分组" name="group_name">
                    <Select 
                        v-model:value="formState.group_name" 
                        placeholder="选择或输入新分组" 
                        :options="groupOptions"
                        allow-clear
                        show-search
                        :filter-option="(input, option: any) => (option?.label || option?.value || '').toLowerCase().indexOf(input.toLowerCase()) >= 0"
                        @search="handleGroupSearch"
                    />
                </Form.Item>
            </div>

            <Form.Item label="描述说明" name="description">
                <Input.TextArea v-model:value="formState.description" :rows="2" placeholder="用于前端显示给用户的填写提示" />
            </Form.Item>

            <Form.Item label="编码权重" name="code_weight" tooltip="生成 SKU 特征码时的排序权重，数字越小越靠前。99表示不重要。">
                <Input type="number" v-model:value="formState.code_weight" style="width: 100%" />
            </Form.Item>

            <Form.Item 
                label="允许自定义值" 
                name="allow_custom" 
                tooltip="开启后，在商品编辑时允许用户输入预设选项之外的值（Select 变为 ComboBox）"
                v-if="formState.type === 'select'"
            >
                <Switch v-model:checked="formState.allow_custom" />
            </Form.Item>

            <Form.Item 
                label="预设选项列表" 
                v-if="formState.type === 'select'"
                required
                class="bg-gray-50 p-4 rounded border border-dashed"
            >
                <div class="flex flex-wrap gap-2 mb-3">
                    <Tag v-for="(opt, index) in formState.options" :key="typeof opt === 'object' ? opt.value : opt" closable @close="removeFormOption(index)">
                        {{ typeof opt === 'object' ? opt.label : opt }}
                    </Tag>
                    <span v-if="!formState.options?.length" class="text-gray-400 italic">暂无选项</span>
                </div>
                <Button type="dashed" block @click="openOptionsEditor">
                    <EditOutlined /> 配置选项内容
                </Button>
            </Form.Item>
        </Form>
      </Modal>

      <!-- 选项配置弹窗 (保持原逻辑，稍作样式微调) -->
      <Modal
        v-model:open="optionsEditorVisible"
        title="配置选项值"
        @ok="handleSaveOptions"
        width="500px"
      >
        <div class="flex gap-2 mb-4 p-4 bg-gray-50 rounded">
            <Input v-model:value="newOptionItem.value" placeholder="存储值 (Value)" style="width: 40%" />
            <Input v-model:value="newOptionItem.label" placeholder="显示名 (Label)" style="width: 40%" />
            <Button type="primary" @click="handleAddOption" :disabled="!newOptionItem.value">添加</Button>
        </div>
        <Table
            :columns="[
                { title: '显示名', dataIndex: 'label' },
                { title: '存储值', dataIndex: 'value' },
                { title: '操作', key: 'action', width: 60 }
            ]"
            :data-source="editingOptions.map(o => typeof o === 'object' ? o : { label: o, value: o })"
            size="small"
            :pagination="false"
            :scroll="{ y: 300 }"
            bordered
        >
            <template #bodyCell="{ column, index }">
                <template v-if="column.key === 'action'">
                    <Button type="text" danger size="small" @click="handleRemoveOption(index)">
                        <DeleteOutlined />
                    </Button>
                </template>
            </template>
        </Table>
      </Modal>
    </div>
  </Page>
</template>

