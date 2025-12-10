<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { 
  Form, 
  Input, 
  Select, 
  InputNumber, 
  Switch, 
  Spin,
  Alert,
  Row,
  Col
} from 'ant-design-vue';
import { getAttributeDefinitionsApi } from '#/api/core/product'; // We might need a category-specific endpoint

const props = defineProps<{
  categoryId?: number;
  value?: Record<string, any>; // v-model:value for attributes object
}>();

const emit = defineEmits(['update:value']);

// --- State ---
const loading = ref(false);
const attributes = ref<any[]>([]); 
const formState = ref<Record<string, any>>(props.value || {});

// --- Methods ---

async function loadCategoryAttributes() {
  if (!props.categoryId) {
      attributes.value = [];
      return;
  }
  
  loading.value = true;
  try {
    // TODO: Call API to get attributes specific to this category
    // For MVP, we might filter client-side or use a mock if the endpoint isn't ready.
    // Assuming getAttributeDefinitionsApi() returns all definitions for now.
    // In real implementation: GET /categories/{id}/attributes
    
    // MOCK DATA for Demo purposes until backend endpoint is confirmed
    // Simulating attributes like: Material, Origin, Warranty
    await new Promise(resolve => setTimeout(resolve, 300)); // Mock latency
    
    attributes.value = [
        { 
            key: 'material', 
            label: '材质 (Material)', 
            type: 'select', 
            options: ['ABS Plastic', 'Aluminum', 'Steel', 'Carbon Fiber'],
            required: true 
        },
        { 
            key: 'warranty', 
            label: '质保期 (Warranty)', 
            type: 'text', 
            placeholder: 'e.g. 1 Year' 
        },
        { 
            key: 'voltage', 
            label: '电压 (Voltage)', 
            type: 'number', 
            suffix: 'V' 
        },
        { 
            key: 'is_waterproof', 
            label: '是否防水', 
            type: 'boolean' 
        }
    ];
    
    // In real app:
    // const res = await getCategoryAttributesApi(props.categoryId);
    // attributes.value = res.filter(attr => attr.scope === 'spu'); // Only show Common Attributes
    
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

watch(() => props.categoryId, () => {
    loadCategoryAttributes();
    // Do not clear formState if switching categories? Usually yes, clear.
    // But if editing, initial load should preserve.
    // We'll let parent handle reset if needed or just keep valid keys.
});

watch(formState, (val) => {
    emit('update:value', val);
}, { deep: true });

watch(() => props.value, (val) => {
    if (val) {
        Object.assign(formState.value, val);
    }
}, { deep: true, immediate: true });

onMounted(() => {
    loadCategoryAttributes();
});
</script>

<template>
  <Spin :spinning="loading">
    <div v-if="attributes.length === 0 && !loading">
       <Alert message="该分类下暂无公共属性配置" type="info" show-icon />
    </div>
    
    <div v-else class="grid grid-cols-2 gap-x-8 gap-y-0">
        <template v-for="attr in attributes" :key="attr.key">
            <Form.Item 
                :label="attr.label" 
                :name="['attributes', attr.key]"
                :rules="attr.required ? [{ required: true, message: '必填项' }] : []"
            >
                <!-- Select -->
                <Select 
                    v-if="attr.type === 'select'"
                    v-model:value="formState[attr.key]"
                    :options="attr.options.map((o: any) => ({ label: o, value: o }))"
                    :placeholder="attr.placeholder || '请选择'"
                    allowClear
                />
                
                <!-- Boolean -->
                <Switch 
                    v-else-if="attr.type === 'boolean'"
                    v-model:checked="formState[attr.key]"
                />
                
                <!-- Number -->
                <InputNumber 
                    v-else-if="attr.type === 'number'"
                    v-model:value="formState[attr.key]"
                    :placeholder="attr.placeholder"
                    style="width: 100%"
                >
                    <template #addonAfter v-if="attr.suffix">{{ attr.suffix }}</template>
                </InputNumber>
                
                <!-- Text / Default -->
                <Input 
                    v-else
                    v-model:value="formState[attr.key]"
                    :placeholder="attr.placeholder"
                />
            </Form.Item>
        </template>
    </div>
  </Spin>
</template>

