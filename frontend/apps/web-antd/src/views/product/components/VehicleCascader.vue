<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { Cascader } from 'ant-design-vue';
import { getBrandsApi, getModelsApi, getYearsApi } from '#/api/core/product';
import type { VehicleNode } from '#/api/core/product';

interface Props {
  value?: (string | number)[];
  disabled?: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['update:value', 'change']);

const options = ref<any[]>([]); 
const loading = ref(false);

// Map API node to Cascader Option
function mapNodeToOption(node: any, isLeaf = false) {
    return {
        value: node.id,
        label: node.name,
        isLeaf: isLeaf,
        loading: false, // Internal loading state for this node
        children: [],   // Needed for 'loadData' to trigger? No, isLeaf=false is enough
        // Metadata
        abbreviation: node.abbreviation,
        code: node.code,
        level_type: node.level_type
    };
}

async function initBrands() {
  loading.value = true;
  try {
    const res = await getBrandsApi();
    const data = (res as any).data || res;
    options.value = data.map((d: any) => mapNodeToOption(d, false));
  } catch (e) {
    console.error('Failed to load brands', e);
  } finally {
    loading.value = false;
  }
}

const onLoadData = async (selectedOptions: any[]) => {
  const targetOption = selectedOptions[selectedOptions.length - 1];
  targetOption.loading = true;

  try {
      let children = [];
      // Level 1 (Make) -> Load Models
      if (targetOption.level_type === 'make' || targetOption.level_type === 'brand') {
          const res = await getModelsApi(targetOption.value);
          children = (res as any).data || res;
          // Models are NOT leaves (Years are next)
          targetOption.children = children.map((c: any) => mapNodeToOption(c, false));
      }
      // Level 2 (Model) -> Load Years
      else if (targetOption.level_type === 'model') {
          const res = await getYearsApi(targetOption.value);
          children = (res as any).data || res;
          // Years ARE leaves
          targetOption.children = children.map((c: any) => mapNodeToOption(c, true));
      }
      
      // If no children found, mark as leaf to stop spinning
      if (!targetOption.children || targetOption.children.length === 0) {
          targetOption.isLeaf = true;
      }
      
      options.value = [...options.value]; // Force update
  } catch (e) {
      console.error(e);
      targetOption.children = [];
  } finally {
      targetOption.loading = false;
  }
};

function handleChange(val: any, selectedOptions: any[]) {
  emit('update:value', val);
  emit('change', val, selectedOptions);
}

// Custom search filter: local only works for loaded items.
// Remote search is hard with Cascader. We might disable search or keep it local-only for loaded.
const filter = (inputValue: string, path: any[]) => {
  return path.some(option => 
    (option.label).toLowerCase().indexOf(inputValue.toLowerCase()) > -1 ||
    (option.abbreviation || '').toLowerCase().indexOf(inputValue.toLowerCase()) > -1
  );
};

onMounted(() => {
  initBrands();
});
</script>

<template>
  <Cascader
    :value="value"
    :options="options"
    :disabled="disabled"
    :loading="loading"
    :load-data="onLoadData"
    placeholder="请选择车型 (Make / Model / Year)"
    :change-on-select="true"
    expand-trigger="click"
    @change="handleChange"
    :show-search="{ filter }"
  >
    <template #displayRender="{ labels, selectedOptions }">
      <span v-for="(label, index) in labels" :key="index">
        {{ label }}
        <span v-if="selectedOptions && selectedOptions[index] && selectedOptions[index].abbreviation" class="text-gray-400 text-xs ml-1">
          ({{ selectedOptions[index].abbreviation }})
        </span>
        <span v-if="index < labels.length - 1"> / </span>
      </span>
    </template>
  </Cascader>
</template>

