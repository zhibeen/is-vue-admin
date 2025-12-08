<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Card, Table, Button, Modal, Form, Input, Select, Switch, message, Space, Tag, Popconfirm, AutoComplete } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined, InfoCircleOutlined, AppstoreOutlined, SettingOutlined } from '@ant-design/icons-vue';
import { getAttributeDefinitionsApi, createAttributeDefinitionApi, updateAttributeDefinitionApi, deleteAttributeDefinitionApi } from '#/api/core/product';
import { getDictItemsApi } from '#/api/core/product'; // Reuse from product api or system api
import type { CategoryAttribute } from '#/api/core/product';

const loading = ref(false);
const dataSource = ref<CategoryAttribute[]>([]);
const modalVisible = ref(false);
const modalTitle = ref('');
const isEditMode = ref(false);

// Dictionary state for groups
const groupOptions = ref<any[]>([]);
const originalGroupOptions = ref<any[]>([]); // Backup for search filtering

const formRef = ref();
const formState = ref<Partial<CategoryAttribute>>({
  id: '',
  key: '',
  label: '',
  type: 'text',
  group_name: '',
  is_global: true,
  code_weight: 99,
  options: []
});

// Options editor state
const optionsEditorVisible = ref(false);
const editingOptions = ref<any[]>([]);
const newOptionItem = ref({ label: '', value: '' });

const columns = [
  { title: 'ID', dataIndex: 'id', width: '80px' },
  { title: '属性名称', dataIndex: 'label', key: 'label' },
  { title: '英文名称', dataIndex: 'name_en', key: 'name_en' }, // New
  { title: '属性Key', dataIndex: 'key', key: 'key' },
  { title: '数据类型', dataIndex: 'type', key: 'type', width: '100px' },
  { title: '默认分组', dataIndex: 'group_name', key: 'group_name', width: '120px' },
  { title: '预设选项', dataIndex: 'options', key: 'options', width: '25%' }, // Added options column
  { title: '排序权重', dataIndex: 'code_weight', key: 'code_weight', width: '100px' },
  { title: '操作', key: 'action', width: '200px', fixed: 'right' as const }
];

onMounted(() => {
  loadData();
  loadGroupDicts();
});

async function loadGroupDicts() {
    try {
        const res = await getDictItemsApi('product_attribute_group');
        // Check structure: if res is array, assume items. 
        // If res.data, use res.data.
        // Based on other APIs, it might be { data: [...] } or just [...].
        // Assuming direct array based on previous logs, but let's be safe.
        const items = Array.isArray(res) ? res : (res as any).data || [];
        
        groupOptions.value = items.map((item: any) => ({
            label: item.label, // Label (e.g. "基本信息")
            value: item.value  // Use Value (e.g. "Basic")
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
        // Add temporary option for custom input
        groupOptions.value = [{ label: val, value: val }, ...originalGroupOptions.value];
    } else {
        groupOptions.value = [...originalGroupOptions.value];
    }
}

async function loadData() {
  loading.value = true;
  try {
    const res = await getAttributeDefinitionsApi();
    dataSource.value = (res as any).data || res;
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
    name_en: '', // New
    description: '', // New
    type: 'text',
    group_name: '',
    is_global: true,
    code_weight: 99,
    options: []
  };
  modalVisible.value = true;
}

function handleEdit(record: CategoryAttribute) {
  isEditMode.value = true;
  modalTitle.value = '编辑属性定义';
  formState.value = { ...record };
  modalVisible.value = true;
}

async function handleDelete(id: string) {
  try {
    await deleteAttributeDefinitionApi(id);
    message.success('删除成功');
    loadData();
  } catch (e) {
    message.error('删除失败，可能已被使用');
  }
}

async function handleSave() {
  try {
    await formRef.value.validate();
    
    // Ensure key matches key_name logic if needed, but backend handles key_name
    // Frontend interface uses 'key', backend uses 'key_name'. 
    // Schema maps key->key_name.
    
    if (isEditMode.value) {
      // Validation for select options
      if (formState.value.type === 'select' && (!formState.value.options || formState.value.options.length === 0)) {
          message.warning('请为下拉选择类型配置预设选项');
          return;
      }

      await updateAttributeDefinitionApi(formState.value.id!, formState.value);
      message.success('更新成功');
    } else {
      // Validation for select options
      if (formState.value.type === 'select' && (!formState.value.options || formState.value.options.length === 0)) {
          message.warning('请为下拉选择类型配置预设选项');
          return;
      }

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
    // Clone options
    const existing = formState.value.options || [];
    editingOptions.value = JSON.parse(JSON.stringify(existing));
    optionsEditorVisible.value = true;
}

function handleAddOption() {
    if (!newOptionItem.value.value) return;
    const val = newOptionItem.value.value;
    const label = newOptionItem.value.label || val;
    
    // Check duplicate
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

function handleSaveOptions() {
    formState.value.options = [...editingOptions.value];
    optionsEditorVisible.value = false;
}
</script>

<template>
  <Page title="商品属性管理">
    <div class="p-4">
      <Card :bordered="false">
        <div class="mb-4 flex justify-between">
          <Button type="primary" @click="handleAdd">
            <PlusOutlined /> 新增属性
          </Button>
          
          <Button type="default" href="/system/dict" target="_blank">
            <AppstoreOutlined /> 属性分组管理
          </Button>
        </div>
        
        <Table
          :columns="columns"
          :data-source="dataSource"
          :loading="loading"
          row-key="id"
          size="middle"
        >
            <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'">
                    <Tag color="blue">{{ record.type }}</Tag>
                </template>
                <template v-if="column.key === 'group_name'">
                    <Tag v-if="record.group_name" color="cyan">
                        {{ groupOptions.find((o: any) => o.value === record.group_name)?.label || record.group_name }}
                    </Tag>
                    <span v-else class="text-gray-400">默认</span>
                </template>
                <template v-if="column.key === 'options'">
                    <template v-if="record.type === 'select'">
                        <div class="flex flex-wrap gap-1 max-h-[60px] overflow-hidden">
                            <Tag v-for="(opt, idx) in (record.options || []).slice(0, 5)" :key="idx" size="small">
                                {{ typeof opt === 'object' ? opt.label : opt }}
                            </Tag>
                            <Tag v-if="(record.options || []).length > 5" size="small" class="bg-gray-50 text-gray-400">
                                +{{ (record.options || []).length - 5 }}
                            </Tag>
                            <span v-if="!(record.options || []).length" class="text-gray-300 italic text-xs">无选项</span>
                        </div>
                    </template>
                    <span v-else class="text-gray-300">-</span>
                </template>
                <template v-if="column.key === 'action'">
                    <Space>
                        <Button type="link" size="small" @click="handleEdit(record)">
                            <EditOutlined /> 编辑
                        </Button>
                        <Popconfirm title="确定要删除吗？" @confirm="handleDelete(record.id)">
                            <Button type="link" size="small" danger>
                                <DeleteOutlined /> 删除
                            </Button>
                        </Popconfirm>
                    </Space>
                </template>
            </template>
        </Table>
      </Card>

      <!-- Edit Modal -->
      <Modal
        v-model:open="modalVisible"
        :title="modalTitle"
        @ok="handleSave"
        width="600px"
      >
        <Form
            ref="formRef"
            :model="formState"
            layout="vertical"
            class="pt-4"
        >
            <Form.Item 
                label="属性名称 (Label)" 
                name="label" 
                :rules="[{ required: true, message: '请输入属性名称' }]"
                tooltip="显示在前端表单中的名称，如 '电压'"
            >
                <Input v-model:value="formState.label" placeholder="如：电压" />
            </Form.Item>

            <Form.Item 
                label="英文名称 (Name EN)" 
                name="name_en" 
                tooltip="业务标准英文名称，用于国际化或报表，如 'Nominal Voltage'"
            >
                <Input v-model:value="formState.name_en" placeholder="如：Nominal Voltage" />
            </Form.Item>

            <Form.Item 
                label="属性Key (Internal Name)" 
                name="key" 
                :rules="[
                    { required: true, message: '请输入唯一Key' },
                    { pattern: /^[a-z][a-z0-9_]*$/, message: 'Key 只能包含小写字母、数字和下划线，且必须以字母开头' }
                ]"
                tooltip="系统内部使用的唯一标识，禁止空格，如 'nominal_voltage'"
            >
                <Input v-model:value="formState.key" placeholder="如：nominal_voltage" :disabled="isEditMode" />
            </Form.Item>
            
            <Form.Item label="数据类型" name="type">
                <Select v-model:value="formState.type">
                    <Select.Option value="text">文本 (Text)</Select.Option>
                    <Select.Option value="textarea">长文本 (Textarea)</Select.Option> <!-- New -->
                    <Select.Option value="number">数字 (Number)</Select.Option>
                    <Select.Option value="boolean">布尔 (Boolean)</Select.Option>
                    <Select.Option value="select">下拉选择 (Select)</Select.Option>
                </Select>
            </Form.Item>

            <Form.Item label="属性描述" name="description">
                <Input.TextArea v-model:value="formState.description" :rows="3" placeholder="属性的详细说明，将显示在 Tooltip 或帮助文档中" />
            </Form.Item>
            
            <Form.Item label="默认分组" name="group_name" tooltip="在分类中添加此属性时的默认分组">
                <div class="flex gap-2">
                    <Select 
                        v-model:value="formState.group_name" 
                        placeholder="选择或输入新分组" 
                        :options="groupOptions"
                        allow-clear
                        show-search
                        :filter-option="(input: string, option: any) => (option?.label || option?.value || '').toLowerCase().indexOf(input.toLowerCase()) >= 0"
                        @search="handleGroupSearch"
                    />
                    <!-- Shortcut to Dict Management (Optional link) -->
                    <Button type="link" size="small" href="/system/dict" target="_blank">
                        <SettingOutlined /> 管理
                    </Button>
                </div>
            </Form.Item>

            <Form.Item label="编码权重" name="code_weight" tooltip="生成 SKU 特征码时的排序权重，越小越靠前">
                <Input type="number" v-model:value="formState.code_weight" />
            </Form.Item>

            <Form.Item label="全局选项" v-if="formState.type === 'select'">
                <div class="bg-gray-50 p-3 rounded border">
                    <div class="flex flex-wrap gap-2 mb-2">
                        <Tag v-for="opt in formState.options" :key="typeof opt === 'object' ? opt.value : opt">
                            {{ typeof opt === 'object' ? opt.label : opt }}
                        </Tag>
                        <span v-if="!formState.options?.length" class="text-gray-400">无预设选项</span>
                    </div>
                    <Button size="small" type="dashed" block @click="openOptionsEditor">
                        <EditOutlined /> 配置选项列表
                    </Button>
                </div>
            </Form.Item>
        </Form>
      </Modal>

      <!-- Options Editor Modal -->
      <Modal
        v-model:open="optionsEditorVisible"
        title="配置全局选项"
        @ok="handleSaveOptions"
        width="500px"
      >
        <div class="flex gap-2 mb-4">
            <Input v-model:value="newOptionItem.value" placeholder="选项值 (Value)" style="width: 40%" />
            <Input v-model:value="newOptionItem.label" placeholder="显示名 (Label)" style="width: 40%" />
            <Button type="primary" @click="handleAddOption" :disabled="!newOptionItem.value">
                <PlusOutlined /> 添加
            </Button>
        </div>
        <div class="max-h-[300px] overflow-y-auto border rounded">
             <Table
                :columns="[
                    { title: '显示名', dataIndex: 'label' },
                    { title: '值', dataIndex: 'value' },
                    { title: '操作', key: 'action', width: '80px' }
                ]"
                :data-source="editingOptions.map(o => typeof o === 'object' ? o : { label: o, value: o })"
                size="small"
                :pagination="false"
            >
                <template #bodyCell="{ column, index }">
                    <template v-if="column.key === 'action'">
                        <Button type="link" danger size="small" @click="handleRemoveOption(index)">删除</Button>
                    </template>
                </template>
            </Table>
        </div>
      </Modal>
    </div>
  </Page>
</template>

