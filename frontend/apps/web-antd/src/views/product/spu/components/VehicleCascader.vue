<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { Cascader } from 'ant-design-vue';
import { getVehicleTreeApi } from '#/api/core/product';

const props = defineProps<{
  value?: string[]; // [make_id, model_id, year_id] or codes
  placeholder?: string;
}>();

const emit = defineEmits(['update:value', 'change']);

const options = ref([]);
const loading = ref(false);

// Load data
async function loadData() {
  loading.value = true;
  try {
    const res = await getVehicleTreeApi();
    // Transform if necessary. Assuming backend returns nested structure:
    // { value: id/code, label: name, children: [...] }
    // If backend returns 'id' as value, we might want 'abbreviation' or 'code' for SPU generation.
    // Let's assume we map it to fit Cascader requirements.
    options.value = transformData(res);
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function transformData(data: any[]) {
  if (!data) return [];
  return data.map(item => ({
    value: item.abbreviation || item.id, // Use abbreviation for code generation if possible
    label: item.name,
    children: transformData(item.children),
    // store full item for extraction
    raw: item 
  }));
}

function handleChange(val: any, selectedOptions: any[]) {
  emit('update:value', val);
  emit('change', val, selectedOptions);
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <Cascader
    :value="value"
    :options="options"
    :placeholder="placeholder || '请选择车型'"
    :loading="loading"
    change-on-select
    @change="handleChange"
    style="width: 100%"
  />
</template>

