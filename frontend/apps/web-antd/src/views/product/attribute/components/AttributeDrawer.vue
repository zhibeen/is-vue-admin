<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { 
  Drawer, 
  Form, 
  Input, 
  Select, 
  Button, 
  Switch, 
  Space, 
  Tag, 
  InputNumber,
  message,
  Popover
} from 'ant-design-vue';
import { 
  PlusOutlined, 
  DeleteOutlined, 
  DragOutlined,
  QuestionCircleOutlined 
} from '@ant-design/icons-vue';
import type { CategoryAttribute } from '#/api/core/product';
import { createAttributeDefinitionApi, updateAttributeDefinitionApi } from '#/api/core/product';

const props = defineProps<{
  groupOptions: { label: string; value: string }[];
}>();

const emit = defineEmits(['success', 'register', 'update:groupOptions']);

// --- State ---
const visible = ref(false);
const isEditMode = ref(false);
const loading = ref(false);
const formRef = ref();

const formState = ref<Partial<CategoryAttribute>>({
  id: '',
  key: '',
  label: '',
  name_en: '',
  description: '',
  type: 'text',
  group_name: '',
  allow_custom: false,
  code_weight: 99,
  options: []
});

// 新增分组状态
const newGroupName = ref('');
const addGroupPopoverVisible = ref(false);

// --- Methods ---

function open(record?: CategoryAttribute) {
  visible.value = true;
  isEditMode.value = !!record;
  
  if (record) {
    // Deep copy
    formState.value = JSON.parse(JSON.stringify(record));
    // Ensure options format
    if (formState.value.options) {
      formState.value.options = formState.value.options.map(o => 
        typeof o === 'object' ? o : { label: o, value: o }
      );
    }
  } else {
    resetForm();
  }
}

function resetForm() {
  formState.value = {
    key: '',
    label: '',
    name_en: '',
    description: '',
    type: 'text',
    group_name: '',
    code_weight: 99,
    options: [],
    allow_custom: false
  };
}

function close() {
  visible.value = false;
  loading.value = false;
}

// --- Key Auto-generation ---
watch(() => formState.value.name_en, (val) => {
  if (!isEditMode.value && val && !formState.value.key) {
    // 简单的自动转换：Rated Voltage -> rated_voltage
    const key = val.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
    if (key) {
        formState.value.key = key;
    }
  }
});

// --- Options Logic ---
function addOption() {
  if (!formState.value.options) formState.value.options = [];
  formState.value.options.push({ label: '', value: '' });
}

function removeOption(index: number) {
  formState.value.options?.splice(index, 1);
}

// --- Group Logic ---
function handleAddGroup() {
    if(!newGroupName.value) return;
    const val = newGroupName.value;
    
    // Check exist
    if (props.groupOptions.some(g => g.value === val)) {
        formState.value.group_name = val;
        addGroupPopoverVisible.value = false;
        return;
    }

    // Emit event to parent to update dict (mock update locally for now)
    // In real world, might need an API call or just local addition until saved
    emit('update:groupOptions', { label: val, value: val });
    formState.value.group_name = val;
    newGroupName.value = '';
    addGroupPopoverVisible.value = false;
}

// --- Submit ---
async function handleSubmit() {
  try {
    loading.value = true;
    await formRef.value.validate();
    
    // Type specific validation
    if (formState.value.type === 'select') {
        if (!formState.value.options || formState.value.options.length === 0) {
            message.warning('下拉类型必须至少配置一个选项');
            return;
        }
        // Filter empty options
        formState.value.options = formState.value.options.filter(o => o.label && o.value);
    } else {
        // Clear options for non-select types to keep clean
        formState.value.options = [];
    }

    if (isEditMode.value) {
      await updateAttributeDefinitionApi(formState.value.id!, formState.value);
      message.success('更新成功');
    } else {
      await createAttributeDefinitionApi(formState.value);
      message.success('创建成功');
    }
    
    close();
    emit('success');
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

// Expose open method
defineExpose({ open });
</script>

<template>
  <Drawer
    v-model:open="visible"
    :title="isEditMode ? '编辑属性定义' : '新增属性定义'"
    width="600"
    :mask-closable="false"
    @close="close"
  >
    <template #extra>
        <Button @click="close">取消</Button>
        <Button type="primary" :loading="loading" @click="handleSubmit" class="ml-2">保存</Button>
    </template>

    <Form
        ref="formRef"
        :model="formState"
        layout="vertical"
    >
        <!-- Basic Info Section -->
        <div class="mb-6">
            <h3 class="text-base font-medium mb-4 text-gray-800 border-l-4 border-primary pl-3">基本信息</h3>
            
            <div class="grid grid-cols-2 gap-4">
                <Form.Item 
                    label="属性名称 (Label)" 
                    name="label" 
                    :rules="[{ required: true, message: '请输入属性名称' }]"
                >
                    <Input v-model:value="formState.label" placeholder="如：额定电压" />
                </Form.Item>

                <Form.Item 
                    name="name_en" 
                >
                    <template #label>
                        英文名称 (EN)
                        <Popover content="用于生成报表或自动生成Key">
                             <QuestionCircleOutlined class="text-gray-400 ml-1" />
                        </Popover>
                    </template>
                    <Input v-model:value="formState.name_en" placeholder="如：Rated Voltage" />
                </Form.Item>
            </div>

            <Form.Item 
                label="属性 Key (Internal ID)" 
                name="key" 
                :rules="[
                    { required: true, message: '请输入唯一Key' },
                    { pattern: /^[a-z][a-z0-9_]*$/, message: '需以小写字母开头，仅含小写字母、数字、下划线' }
                ]"
            >
                <Input v-model:value="formState.key" :disabled="isEditMode" placeholder="system_unique_key">
                    <template #prefix>attr_</template>
                </Input>
            </Form.Item>

            <Form.Item label="所属分组" name="group_name">
                <div class="flex gap-2">
                    <Select 
                        v-model:value="formState.group_name" 
                        placeholder="选择分组" 
                        :options="props.groupOptions"
                        allow-clear
                        show-search
                        class="flex-1"
                    />
                    <Popover v-model:open="addGroupPopoverVisible" trigger="click" placement="bottomRight">
                        <template #content>
                            <div class="flex gap-2 p-1">
                                <Input v-model:value="newGroupName" placeholder="新分组名称" size="small" />
                                <Button type="primary" size="small" @click="handleAddGroup">确定</Button>
                            </div>
                        </template>
                        <Button>
                            <PlusOutlined />
                        </Button>
                    </Popover>
                </div>
            </Form.Item>
            
            <Form.Item label="描述说明" name="description">
                <Input.TextArea v-model:value="formState.description" :rows="2" placeholder="用于前端显示填写提示" />
            </Form.Item>
        </div>

        <!-- Data Config Section -->
        <div class="mb-6">
            <h3 class="text-base font-medium mb-4 text-gray-800 border-l-4 border-primary pl-3">数据配置</h3>

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

                <Form.Item label="排序权重" name="code_weight">
                    <InputNumber v-model:value="formState.code_weight" class="w-full" :min="0" :max="999" />
                </Form.Item>
            </div>

             <!-- Select Options Editor (Inline) -->
            <div v-if="formState.type === 'select'" class="bg-gray-50 p-4 rounded border border-dashed border-gray-300">
                <div class="flex justify-between items-center mb-3">
                    <span class="font-medium text-gray-700">预设选项列表</span>
                    <Space>
                        <span class="text-xs text-gray-500">允许自定义值</span>
                        <Switch v-model:checked="formState.allow_custom" size="small" />
                    </Space>
                </div>

                <div class="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                    <div 
                        v-for="(opt, index) in formState.options" 
                        :key="index"
                        class="flex items-center gap-2 group"
                    >
                        <div class="cursor-move text-gray-300 hover:text-gray-500">
                             <DragOutlined />
                        </div>
                        <Input v-model:value="opt.label" placeholder="显示名 (Label)" size="small" />
                        <Input v-model:value="opt.value" placeholder="存储值 (Value)" size="small" />
                        
                        <Button 
                            type="text" 
                            danger 
                            size="small" 
                            @click="removeOption(index)"
                            class="opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <DeleteOutlined />
                        </Button>
                    </div>

                    <Button type="dashed" block size="small" @click="addOption">
                        <PlusOutlined /> 添加选项
                    </Button>
                </div>
            </div>
        </div>
    </Form>
  </Drawer>
</template>

