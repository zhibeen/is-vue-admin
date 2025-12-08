<script lang="ts" setup>
import { ref, onMounted, computed, watch } from 'vue';
import { Page } from '@vben/common-ui';
import { Popover as APopover } from 'ant-design-vue'; // Import Popover explicitly if needed, or rely on global registration. 
// Assuming global registration or auto-import. If not, add import.
// Actually, let's just use Popover from ant-design-vue in import list.
import { Card, Table, Button, Modal, Form, Input, Switch, message, Space, Tag, Row, Col, Select, Radio, Tabs, Popover } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined, CloseOutlined, ArrowLeftOutlined, ArrowRightOutlined, InfoCircleOutlined, ReloadOutlined, LoadingOutlined, AppstoreAddOutlined, AppstoreOutlined } from '@ant-design/icons-vue'; // eslint-disable-line no-unused-vars

import { getCategoriesApi, createCategoryApi, updateCategoryApi, deleteCategoryApi, migrateCategoryApi, getProductRulesApi, getCategoryAttributesApi, getAttributeDefinitionsApi, addCategoryAttributeApi, removeCategoryAttributeApi, updateCategoryAttributeApi, copyCategoryAttributesApi, getDictItemsApi } from '#/api/core/product';
import { getDictsApi } from '#/api/system/dict'; // Added
import { Cascader } from 'ant-design-vue'; // Import Cascader for copy selector

import type { Category } from '#/api/core/product';

// ... (Constants & State) ...

// Inheritance Computed
const effectiveIdentity = computed(() => {
    if (useInheritedIdentity.value && parentCategory.value?.spu_config?.vehicle_link) {
        return parentCategory.value.spu_config.vehicle_link;
    }
    return formState.value.spu_config.vehicle_link;
});

const effectiveTemplate = computed(() => {
    if (useInheritedTemplate.value && parentCategory.value?.spu_config?.template) {
        return parentCategory.value.spu_config.template;
    }
    return formState.value.spu_config.template; // Note: This is string
});

const effectiveBusinessType = computed(() => {
    return formState.value.business_type;
});

// --- Level Visualization Logic ---
const vehicleLevelMeta = ref<Record<string, { label: string, order: number }>>({});

const vehicleLevelOptions = computed(() => {
    return Object.entries(vehicleLevelMeta.value)
        .map(([value, info]) => ({ value, label: info.label, order: info.order }))
        .sort((a, b) => a.order - b.order);
});

async function loadDicts() {
    try {
        const dicts = await getDictsApi();
        const vehicleDict = dicts.find((d: any) => d.code === 'vehicle_level_type');
        if (vehicleDict && vehicleDict.value_options) {
            const metaMap: Record<string, { label: string, order: number }> = {};
            vehicleDict.value_options.forEach((opt: any) => {
                metaMap[opt.value] = {
                    label: opt.label,
                    order: opt.meta?.order || 999 
                };
            });
            vehicleLevelMeta.value = metaMap;
        } else {
            // Fallback defaults
            vehicleLevelMeta.value = {
                'make': { label: '制造商', order: 10 },
                'series': { label: '车系', order: 15 },
                'model': { label: '车型', order: 20 },
                'year': { label: '年份', order: 30 },
            };
        }
    } catch (e) {
        console.error('Failed to load dicts', e);
    }
}

function getLevelLabel(val: string) {
    return vehicleLevelMeta.value[val]?.label || val;
}

const sortedVehicleLevels = computed(() => {
    const levels = formState.value.spu_config.vehicle_link.levels || [];
    return [...levels].sort((a, b) => {
        const orderA = vehicleLevelMeta.value[a]?.order || 999;
        const orderB = vehicleLevelMeta.value[b]?.order || 999;
        return orderA - orderB;
    });
});

// --- Constants ---
// Removed hardcoded constants
const businessTypes = ref<{ label: string; value: string }[]>([]);

// --- State ---
const treeData = ref<Category[]>([]);
const expandedRowKeys = ref<string[]>([]);
const loading = ref(false);
const modalVisible = ref(false);
const modalTitle = ref('');
const isEditMode = ref(false);
const activeTab = ref('basic'); // Added Tab State

// Inheritance Logic
const parentCategory = ref<Category | null>(null);
const useInheritedIdentity = ref(false);
const useInheritedTemplate = ref(false);

// Remove redundant Attribute Modal logic since it's merged
// const attrModalVisible = ref(false); // Removed
// const currentAttrCategory = ref<Category | null>(null); // Keep as context
// ...

// Logic to load definitions if not loaded (Triggered on mount or lazily)
// We can load them when 'attributes' tab is activated if empty
watch(activeTab, async (val) => {
    if (val === 'attributes') {
        if (allAttributeDefs.value.length === 0) {
             try {
                const res = await getAttributeDefinitionsApi();
                allAttributeDefs.value = (res as any).data || res;
             } catch (e) { console.error(e); }
        }
        if (currentAttrCategory.value) {
            loadCategoryAttributes();
        }
    }
});

const formRef = ref();
const formState = ref({
  id: '',
  parent_id: null as string | null,
  name: '',
// ... (rest same)
  name_en: '',
  code: '',
  abbreviation: '',
  business_type: '', // Default will be set on load or add
  description: '',
  spu_config: {
      template: '',
      vehicle_link: {
          enabled: false,
          levels: [] as string[]
      }
  },
  is_active: true,
  sort_order: 0,
  is_leaf: false
});

// --- Template Builder Logic ---
const templateSegments = ref<string[]>([]);

const availableVars = [
    { label: '分类 (Cat)', value: '{cat}', color: 'blue' },
    { label: '车型身份 (Vehicle)', value: '{vehicle}', color: 'cyan' },
    { label: '规格 (Spec)', value: '{spec}', color: 'magenta' },
    { label: '材质 (Material)', value: '{material}', color: 'geekblue' },
    { label: '电压 (Voltage)', value: '{voltage}', color: 'gold' },
];

// Define which variables trigger vehicle linkage
const vehicleVars = ['{vehicle}'];

// Helper: Sync Levels from Template (Unused removed)

// Sync: Array -> String
function updateTemplateString() {
    formState.value.spu_config.template = templateSegments.value.join('-');
}

// Action: Add
function addTemplateSegment(val: string) {
    if (useInheritedTemplate.value) {
        message.warning('当前为继承模式，请切换到自定义模式后编辑');
        return;
    }
    templateSegments.value.push(val);
    updateTemplateString();
}

// Action: Remove
function removeTemplateSegment(index: number) {
    if (useInheritedTemplate.value) return;
    templateSegments.value.splice(index, 1);
    updateTemplateString();
}

// Action: Move
function moveTemplateSegment(index: number, direction: number) {
    if (direction === -1 && index > 0) {
        const temp = templateSegments.value[index]!;
        templateSegments.value[index] = templateSegments.value[index - 1]!;
        templateSegments.value[index - 1] = temp;
    } else if (direction === 1 && index < templateSegments.value.length - 1) {
        const temp = templateSegments.value[index]!;
        templateSegments.value[index] = templateSegments.value[index + 1]!;
        templateSegments.value[index + 1] = temp;
    }
    updateTemplateString();
}

// --- SPU Preview Logic ---
const previewSku = ref('');
const isPreviewLoading = ref(false);

async function refreshSkuPreview() {
    // Basic validation
    if (!formState.value.spu_config.template) {
        previewSku.value = '';
        return;
    }
    
    isPreviewLoading.value = true;
    try {
        // Simulation logic (Frontend only for now, can be moved to backend for accuracy)
        let simulated = formState.value.spu_config.template;
        
        // Replace known variables with mock data
        const mocks: Record<string, string> = {
            '{cat}': formState.value.abbreviation || 'HL',
            '{vehicle}': 'CHE-SIL-07-13', // Mock vehicle code
            '{spec}': 'STD',
            '{material}': 'ABS',
            '{voltage}': '12V'
        };
        
        // If vehicle link enabled, construct vehicle part
        if (formState.value.spu_config.vehicle_link.enabled) {
            // Mock based on levels
            // levels: ['make', 'model', 'year'] -> CHE-SIL-07-13
            // This logic mirrors backend CodeBuilder
        }
        
        // Replace
        for (const [key, val] of Object.entries(mocks)) {
            simulated = simulated.replace(key, val);
        }
        
        // Handle custom attributes not in mocks? 
        // For preview, we just keep the variable or replace with '???'
        
        previewSku.value = simulated;
    } catch (e) {
        previewSku.value = '预览生成失败';
    } finally {
        isPreviewLoading.value = false;
    }
}

// Watch template changes to refresh preview
watch(() => formState.value.spu_config.template, () => {
    if (!useInheritedTemplate.value) {
        refreshSkuPreview();
    }
}, { deep: true }); // Removed debounce option, use lodash debounce if needed or rely on input event

// Watch inheritance changes
watch(useInheritedTemplate, (val) => {
    if (val) {
        // If inherited, use parent's effective template for simulation
        // (Wait for simulated backend calculation or just use displayed string)
        previewSku.value = '继承模式下将使用父级规则生成 (HL-CHE-SIL-07-13-...)';
    } else {
        refreshSkuPreview();
    }
});

// --- Copy Configuration Logic ---
const copySourceId = ref<string[]>([]); // Cascader value is array path
const copyLoading = ref(false);

// Flatten tree for Cascader options
// We need { label, value, children } structure
function transformToCascader(nodes: Category[]): any[] {
    return nodes.map(node => ({
        label: node.name,
        value: node.id,
        children: node.children && node.children.length > 0 ? transformToCascader(node.children) : undefined,
        disabled: node.id === formState.value.id // Disable self
    }));
}

const copyOptions = computed(() => transformToCascader(treeData.value));

async function handleCopyConfig() {
    if (!currentAttrCategory.value || copySourceId.value.length === 0) return;
    
    const sourceId = copySourceId.value[copySourceId.value.length - 1]; // Get last ID
    if (!sourceId) return; // Guard
    
    Modal.confirm({
        title: '确认复制',
        content: '这将覆盖当前分类的自定义属性配置。确定要从选定分类复制吗？',
        onOk: async () => {
            try {
                copyLoading.value = true;
                await copyCategoryAttributesApi(currentAttrCategory.value!.id, sourceId);
                message.success('配置已复制');
                // Reload attributes
                loadCategoryAttributes();
                copySourceId.value = []; // Reset selection
            } catch (e) {
                message.error('复制失败');
            } finally {
                copyLoading.value = false;
            }
        }
    });
}

const columns = [
  { title: '分类名称 (中文)', dataIndex: 'name', key: 'name', width: '15%' },
  { title: '业务线', dataIndex: 'business_type', key: 'business_type', width: '8%' },
  { title: '英文名称', dataIndex: 'name_en', key: 'name_en', width: '12%' },
  { title: 'SKU编码', dataIndex: 'code', key: 'code', width: '8%' },
  { title: '特征码', dataIndex: 'abbreviation', key: 'abbreviation', width: '8%' },
  { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: '6%' },
  { title: '状态', key: 'status', width: '8%' },
  { title: '类型', key: 'type', width: '8%' },
  { title: '描述', dataIndex: 'description', key: 'description', width: '12%', ellipsis: true },
  { title: '操作', key: 'action', minWidth: 200, fixed: 'right' as const }, // Fixed width for actions
];

// --- Lifecycle ---
onMounted(() => {
  loadData();
  loadDicts();
});

async function loadData() {
  loading.value = true;
  try {
    // Load rules if empty
    if (businessTypes.value.length === 0) {
        const rules = await getProductRulesApi();
        businessTypes.value = rules.map((r: any) => ({
            label: r.name,
            value: r.business_type
        }));
    }

    const res = await getCategoriesApi();
    treeData.value = res; // Direct assignment, pass-through data
    
    // Auto expand all rows by default
    const keys: string[] = [];
    const traverse = (items: Category[]) => {
      items.forEach(item => {
        keys.push(item.id);
        if (item.children) {
          traverse(item.children);
        }
      });
    };
    traverse(treeData.value);
    expandedRowKeys.value = keys;
  } catch (e) {
    message.error('加载分类失败');
  } finally {
    loading.value = false;
  }
}

// transformData function removed

// Helper: Find Category
const findCategory = (nodes: Category[], id: string): Category | null => {
    for (const node of nodes) {
        if (node.id === id) return node;
        if (node.children) {
            const found = findCategory(node.children, id);
            if (found) return found;
        }
    }
    return null;
};

// --- Actions ---
function handleAdd(parentId: string | null = null) {
  isEditMode.value = false;
  modalTitle.value = parentId ? '新增子分类' : '新增一级分类';
  
  // Find Parent
  parentCategory.value = parentId ? findCategory(treeData.value, parentId) : null;
  currentAttrCategory.value = null; // No attr context for new category
  activeTab.value = 'basic'; // Reset tab
  
  // Inheritance Defaults: New child defaults to inherit ONLY if parent exists
  const hasParent = !!parentCategory.value;
  useInheritedIdentity.value = hasParent;
  useInheritedTemplate.value = hasParent;

  // Try to find parent to inherit business_type
  let inheritedType = ''; 
  if (parentCategory.value && parentCategory.value.business_type) {
      inheritedType = parentCategory.value.business_type;
  } else {
      if (businessTypes.value.length > 0 && businessTypes.value[0]) {
          inheritedType = businessTypes.value[0].value;
      }
  }

  formState.value = {
    id: '',
    parent_id: parentId,
    name: '',
    name_en: '',
    code: '',
    abbreviation: '',
    business_type: inheritedType,
    description: '',
    spu_config: {
        template: '',
        vehicle_link: { enabled: false, levels: [] }
    },
    is_active: true,
    sort_order: 0,
    is_leaf: !!parentId 
  };
  
  // Initialize template builder
  templateSegments.value = [];
  
  modalVisible.value = true;
}

function handleEdit(record: Category) {
  isEditMode.value = true;
  modalTitle.value = '编辑分类';
  
  // Find Parent
  parentCategory.value = record.parent_id ? findCategory(treeData.value, record.parent_id) : null;
  currentAttrCategory.value = record; // Set Attr Context
  activeTab.value = 'basic'; // Reset tab

  // Determine Inheritance Mode
  const ownConfig = record.spu_config;
  // If own config is empty/null, assume inherited
  const hasOwnConfig = ownConfig && Object.keys(ownConfig).length > 0;
  const hasParent = !!parentCategory.value;
  
  if (hasParent) {
      useInheritedIdentity.value = !hasOwnConfig; 
      useInheritedTemplate.value = !hasOwnConfig;
  } else {
      // Root category must be Custom
      useInheritedIdentity.value = false;
      useInheritedTemplate.value = false;
  }
  
  // Get Effective Config (Backend calculated or fallback)
  // We prioritize effective_spu_config from backend if available
  const effective = (record as any).effective_spu_config || record.spu_config || {};
  
  // If record has no business_type (legacy data), fallback to first available
  const bType = record.business_type || ((businessTypes.value.length > 0 && businessTypes.value[0]) ? businessTypes.value[0].value : '');
  
  // Parse template string to array (Using EFFECTIVE config)
  const tpl = effective.template || '';
  templateSegments.value = tpl ? tpl.split('-') : [];
  
  formState.value = { 
    id: record.id,
    parent_id: record.parent_id,
    name: record.name,
    name_en: record.name_en || '',
    code: record.code,
    abbreviation: record.abbreviation || '',
    business_type: bType,
    description: record.description || '',
    spu_config: {
        template: tpl,
        vehicle_link: {
            enabled: effective.vehicle_link?.enabled || false,
            levels: effective.vehicle_link?.levels || []
        }
    },
    is_active: record.is_active,
    sort_order: record.sort_order,
    is_leaf: record.is_leaf
  };
  modalVisible.value = true;
}

function handleDelete(id: string) {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个分类吗？如果是父分类，子分类也会被影响。',
    onOk: async () => {
      try {
        await deleteCategoryApi(id);
        message.success('删除成功');
        loadData();
      } catch (e) {
        // Error handled by request interceptor usually
      }
    }
  });
}

async function handleSave() {
  try {
    await formRef.value.validate();
    
    // Sort vehicle levels before sending
    if (formState.value.spu_config?.vehicle_link?.levels) {
        formState.value.spu_config.vehicle_link.levels.sort((a: string, b: string) => {
            const orderA = vehicleLevelMeta.value[a]?.order || 999;
            const orderB = vehicleLevelMeta.value[b]?.order || 999;
            return orderA - orderB;
        });
    }
    
    // Create payload and remove id as it's passed in URL or not needed for create
    const { id, ...payloadData } = formState.value; 
    const payload = { ...payloadData };

    // Handle Inheritance: If fully inherited, send null to backend
    if (useInheritedIdentity.value && useInheritedTemplate.value) {
        (payload as any).spu_config = null;
    }

    if (isEditMode.value) {
        try {
            await updateCategoryApi(id, payload);
            message.success('更新成功');
            modalVisible.value = false;
            loadData();
        } catch (error: any) {
            // Check for migration requirement code 30010
            const res = error?.response?.data || error?.data || error;
            if (res?.code === 30010) {
                 Modal.confirm({
                    title: '需要迁移数据',
                    content: `检测到该分类下有 ${res.data.product_count} 个商品。是否自动创建子分类 "${res.data.suggested_child_name}" 并迁移这些商品？`,
                    onOk: async () => {
                        try {
                            await migrateCategoryApi(formState.value.id);
                            message.success('迁移并更新成功');
                            modalVisible.value = false;
                            loadData();
                        } catch (e) {
                             console.error(e);
                        }
                    }
                 });
                 // Stop execution here, let user interaction decide
                 return;
            }
            throw error;
        }
    } else {
        await createCategoryApi(payload);
        message.success('创建成功');
        modalVisible.value = false;
        loadData();
    }
  } catch (e) {
    // validation failed or api error
    console.error(e);
  }
}

// --- Attribute Management Logic ---
// const attrModalVisible = ref(false); // Merged into main modal
const currentAttrCategory = ref<Category | null>(null);
const categoryAttributes = ref<any[]>([]);
const allAttributeDefs = ref<any[]>([]);
const groupDictOptions = ref<any[]>([]); // New Dict Options
const attrLoading = ref(false);
const addingAttr = ref(false);
const newAttrForm = ref<{ attribute_id: number | undefined; is_required: boolean; group_name: string | undefined }>({
    attribute_id: undefined,
    is_required: false,
    group_name: undefined
});

// Group Attributes
const groupedSelfAttributes = computed(() => {
    const groups: Record<string, any[]> = { '默认分组': [] };
    
    selfAttributes.value.forEach(attr => {
        const gName = attr.group_name || '默认分组';
        if (!groups[gName]) groups[gName] = [];
        groups[gName].push(attr);
    });
    
    // Sort logic within groups? Currently by display_order from backend
    return groups;
});

const groupNames = computed(() => Object.keys(groupedSelfAttributes.value).sort((a) => a === '默认分组' ? -1 : 1));

// Split attributes for UI Grouping
const inheritedAttributes = computed(() => {
    return categoryAttributes.value.filter(attr => attr.origin !== 'self');
});

const selfAttributes = computed(() => {
    return categoryAttributes.value.filter(attr => attr.origin === 'self');
});

const selfAttributeColumns = [
    { title: '属性名称', dataIndex: 'label', key: 'label', width: '20%' },
    { title: 'Key', dataIndex: 'key', key: 'key', width: '15%' },
    { title: '必填', key: 'is_required', width: '10%' },
    { title: '参与编码', key: 'include_in_code', width: '10%' },
    { title: '选项预览 (Options)', key: 'options', width: '30%' },
    { title: '操作', key: 'action', width: '15%' }
];

const attributeOptions = computed(() => {
    return allAttributeDefs.value.map(def => ({
        label: `${def.label} (${def.key})`, // def from definitions API returns 'key'
        value: def.id,
        // Check both key and key_name to be safe, but usually it's 'key' from API
        disabled: categoryAttributes.value.some(a => (a.key || a.key_name) === (def.key || def.key_name))
    }));
});

async function loadCategoryAttributes() {
    if (!currentAttrCategory.value) return;
    const res = await getCategoryAttributesApi(currentAttrCategory.value.id, { inheritance: true });
    categoryAttributes.value = (res as any).data || res;
    
    // Lazy load group dicts if needed
    if (groupDictOptions.value.length === 0) {
        try {
            const dictRes = await getDictItemsApi('product_attribute_group');
            groupDictOptions.value = dictRes.map((d: any) => ({ label: d.label, value: d.value }));
        } catch (e) { console.error(e); }
    }
}

async function handleAddAttribute() {
    if (!newAttrForm.value.attribute_id || !currentAttrCategory.value) return;
    try {
        addingAttr.value = true;
        await addCategoryAttributeApi(currentAttrCategory.value.id, {
            attribute_id: newAttrForm.value.attribute_id,
            is_required: newAttrForm.value.is_required,
            group_name: newAttrForm.value.group_name,
            display_order: (categoryAttributes.value.length + 1) * 10 
        });
        message.success('关联成功');
        newAttrForm.value = { attribute_id: undefined, is_required: false, group_name: undefined };
        await loadCategoryAttributes();
    } catch(e) {
        message.error('关联失败或已存在');
    } finally {
        addingAttr.value = false;
    }
}

// Quick Group Edit
async function handleUpdateGroup(record: any, groupName: string) {
    if (!currentAttrCategory.value) return;
    try {
        await updateCategoryAttributeApi(currentAttrCategory.value.id, record.id, {
            group_name: groupName
        });
        message.success('分组已更新');
        await loadCategoryAttributes(); // Reload to refresh grouping
    } catch(e) {
        message.error('更新失败');
    }
}

async function handleToggleRequired(record: any, checked: boolean) {
    if (!currentAttrCategory.value) return;
    try {
        // Optimistic UI update
        record.is_required = checked;
        
        await updateCategoryAttributeApi(currentAttrCategory.value.id, record.id, {
            is_required: checked
        });
        message.success('更新成功');
    } catch(e) {
        // Revert on failure
        record.is_required = !checked;
        message.error('更新失败');
    }
}

async function handleToggleIncludeCode(record: any, checked: boolean) {
    if (!currentAttrCategory.value) return;
    try {
        // Optimistic UI update
        record.include_in_code = checked;
        
        await updateCategoryAttributeApi(currentAttrCategory.value.id, record.id, {
            include_in_code: checked
        });
        message.success('更新成功');
    } catch(e) {
        // Revert on failure
        record.include_in_code = !checked;
        message.error('更新失败');
    }
}

async function handleRemoveAttribute(attr: any) {
    if (!currentAttrCategory.value) return;
    try {
        await removeCategoryAttributeApi(currentAttrCategory.value.id, attr.id);
        message.success('移除成功');
        await loadCategoryAttributes();
    } catch(e) {
        message.error('移除失败');
    }
}

// --- Options Configuration Logic ---
const optionsModalVisible = ref(false);
const currentEditAttr = ref<any>(null);
const useGlobalOptions = ref(true);
const editingOptions = ref<any[]>([]);
const newOptionItem = ref({ label: '', value: '' });

function handleConfigOptions(record: any) {
    currentEditAttr.value = record;
    // record.override_options is null if inheriting (Global)
    useGlobalOptions.value = record.override_options === null;
    
    // Load effective options to start with
    // Ensure we work with a deep copy
    const source = record.effective_options || [];
    // Normalize source: if strings, convert to objects? 
    // For simplicity, let's keep them as is, but UI might need consistency.
    // Our System Dicts use { label, value, ... }. 
    // AttributeDefinition options are JSONB.
    // Let's assume they are list of objects { label, value } or strings.
    
    editingOptions.value = JSON.parse(JSON.stringify(source));
    optionsModalVisible.value = true;
}

function handleAddOption() {
    if (!newOptionItem.value.value) return;
    
    const val = newOptionItem.value.value;
    const label = newOptionItem.value.label || val;
    
    // Check duplicate
    // Support both string and object options
    const exists = editingOptions.value.some((o: any) => {
        const v = typeof o === 'object' ? o.value : o;
        return v === val;
    });
    
    if (exists) {
        message.warning('选项值已存在');
        return;
    }
    
    // Add as object standard
    editingOptions.value.push({ label, value: val });
    newOptionItem.value = { label: '', value: '' };
}

function handleRemoveOption(index: number) {
    editingOptions.value.splice(index, 1);
}

async function handleSaveOptions() {
    if (!currentAttrCategory.value || !currentEditAttr.value) return;
    
    try {
        const payload = {
            options: useGlobalOptions.value ? null : editingOptions.value
        };
        
        await updateCategoryAttributeApi(
            currentAttrCategory.value.id, 
            currentEditAttr.value.id, 
            payload
        );
        
        message.success('选项配置已更新');
        optionsModalVisible.value = false;
        loadCategoryAttributes(); // Refresh
    } catch (e) {
        console.error(e);
        message.error('保存失败');
    }
}
</script>

<template>
  <Page title="品名分类管理">
    <div class="p-4">
      <Card :bordered="false">
        <div class="mb-4">
          <Button type="primary" @click="handleAdd(null)">
            <PlusOutlined /> 新增一级分类
          </Button>
        </div>
        
        <Table
          :columns="columns"
          :data-source="treeData"
          :loading="loading"
          row-key="id"
          :expand-row-by-click="false"
          v-model:expandedRowKeys="expandedRowKeys"
        >
           <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'business_type'">
                  <Tag color="cyan" v-if="record.business_type === 'vehicle'">汽配</Tag>
                  <Tag color="purple" v-else-if="record.business_type === 'general'">通用</Tag>
                  <Tag color="orange" v-else-if="record.business_type === 'electronics'">电子</Tag>
                  <Tag color="default" v-else>{{ record.business_type }}</Tag>
              </template>
              <template v-if="column.key === 'code'">
                  <Tag color="blue">{{ record.code }}</Tag>
              </template>
              <template v-if="column.key === 'abbreviation'">
                  <Tag color="orange" v-if="record.abbreviation">{{ record.abbreviation }}</Tag>
              </template>
              <template v-if="column.key === 'status'">
                  <Tag :color="record.is_active ? 'success' : 'error'">{{ record.is_active ? '启用' : '禁用' }}</Tag>
              </template>
              <template v-if="column.key === 'type'">
                  <Tag v-if="record.is_leaf" color="green">末级类目</Tag>
                  <Tag v-else color="blue">分类目录</Tag>
              </template>
              <template v-if="column.key === 'action'">
                  <Space>
                      <Button type="link" size="small" @click="handleEdit(record as Category)">
                          <EditOutlined /> 编辑
                      </Button>
                      <!-- Only allow adding children for folders (!is_leaf) -->
                      <Button type="link" size="small" @click="handleAdd(record.id)" v-if="!record.is_leaf">
                          <PlusOutlined /> 添加子类
                      </Button>
                      <Button type="link" size="small" danger @click="handleDelete(record.id)">
                          <DeleteOutlined /> 删除
                      </Button>
                  </Space>
              </template>
           </template>
        </Table>
      </Card>

      <!-- Edit/Create Modal -->
      <Modal
        v-model:open="modalVisible"
        :title="modalTitle"
        @ok="handleSave"
        width="800px"
      >
        <Tabs v-model:activeKey="activeTab">
          <!-- TAB 1: Basic Info -->
          <Tabs.TabPane key="basic" tab="基础信息">
            <Form
                ref="formRef"
                :model="formState"
                layout="vertical"
                class="pt-4"
            >
                <Form.Item label="分类名称 (中文)" name="name" :rules="[{ required: true, message: '请输入分类名称' }]">
                    <Input v-model:value="formState.name" placeholder="例如：前大灯" />
                </Form.Item>

                <Form.Item label="英文名称" name="name_en" :rules="[{ required: true, message: '请输入英文名称' }]">
                    <Input v-model:value="formState.name_en" placeholder="例如：Headlight (会自动格式化)" />
                </Form.Item>
                
                <Form.Item label="业务类型" name="business_type" tooltip="不同业务类型使用不同的SKU编码规则">
                    <Select v-model:value="formState.business_type" :disabled="!!formState.parent_id">
                        <Select.Option v-for="type in businessTypes" :key="type.value" :value="type.value">
                            {{ type.label }}
                        </Select.Option>
                    </Select>
                </Form.Item>
                
                <Row :gutter="16">
                    <Col :span="12">
                        <Form.Item 
                            label="SKU分类码" 
                            name="code" 
                            :rules="[
                            { required: true, message: '请输入分类编码' },
                            { 
                                pattern: formState.business_type === 'vehicle' ? /^[1-9]\d{2}$/ : /^[A-Za-z0-9]+$/,
                                message: formState.business_type === 'vehicle' ? '汽配分类必须为3位数字' : '编码只能包含字母和数字'
                            }
                            ]"
                            :tooltip="formState.business_type === 'vehicle' ? '汽配：3位数字，如 101' : '通用：建议字母开头，如 E01'"
                        >
                            <Input v-model:value="formState.code" :placeholder="formState.business_type === 'vehicle' ? '101' : 'E01'" />
                        </Form.Item>
                    </Col>
                    <Col :span="12">
                        <Form.Item 
                            label="特征码 (字母)" 
                            name="abbreviation" 
                            :rules="[{ required: true, message: '请输入业务特征码' }]"
                            tooltip="用于业务识别的字母缩写，如 HL"
                        >
                            <Input v-model:value="formState.abbreviation" placeholder="如 HL" />
                        </Form.Item>
                    </Col>
                </Row>
                
                <Form.Item label="节点类型" name="is_leaf" tooltip="末级类目才能关联具体产品，且不可再添加子分类">
                    <Switch 
                        v-model:checked="formState.is_leaf" 
                        checked-children="末级类目" 
                        un-checked-children="分类目录" 
                    />
                </Form.Item>
                
                <Form.Item label="状态" name="is_active">
                    <Switch v-model:checked="formState.is_active" checked-children="启用" un-checked-children="禁用" />
                </Form.Item>

                <Form.Item label="排序" name="sort_order">
                    <Input type="number" v-model:value="formState.sort_order" />
                </Form.Item>

                <Form.Item label="描述" name="description">
                    <Input.TextArea v-model:value="formState.description" :rows="3" />
                </Form.Item>
            </Form>
          </Tabs.TabPane>

          <!-- TAB 2: Rules -->
          <Tabs.TabPane key="rules" tab="SPU规则">
            <Form layout="vertical" class="pt-4">
                <!-- Block A: Identity Rules -->
                <div v-if="effectiveBusinessType === 'vehicle'">
                    <h3 class="mb-4 font-bold">车型识别规则 (Vehicle Identity Rules)</h3>
                    <Form.Item label="配置模式">
                        <Radio.Group v-model:value="useInheritedIdentity">
                            <Radio :value="true" v-if="parentCategory">继承自父级</Radio>
                            <Radio :value="false">自定义配置</Radio>
                        </Radio.Group>
                    </Form.Item>

                    <div v-if="useInheritedIdentity" class="bg-gray-50 p-3 rounded mb-4 text-gray-500">
                        <InfoCircleOutlined /> 继承配置: 
                        <span v-if="effectiveIdentity && effectiveIdentity.enabled">
                            关联层级: <Tag v-for="l in effectiveIdentity.levels" :key="l">{{ l }}</Tag>
                        </span>
                        <span v-else>未启用身份关联</span>
                    </div>

                    <div v-else>
                        <Form.Item label="启用车型关联">
                            <Switch v-model:checked="formState.spu_config.vehicle_link.enabled" />
                        </Form.Item>
                        <Form.Item 
                            v-if="formState.spu_config.vehicle_link.enabled"
                            label="关联层级"
                        >
                            <Select v-model:value="formState.spu_config.vehicle_link.levels" mode="multiple">
                                <Select.Option v-for="opt in vehicleLevelOptions" :key="opt.value" :value="opt.value">
                                    {{ opt.label }}
                                </Select.Option>
                            </Select>
                        </Form.Item>

                        <!-- Level Chain Visualizer -->
                        <div class="ml-[120px] mb-4" v-if="formState.spu_config.vehicle_link.enabled && formState.spu_config.vehicle_link.levels.length > 0">
                            <div class="text-xs text-gray-400 mb-1">层级结构预览:</div>
                            <div class="flex items-center flex-wrap gap-2">
                                <template v-for="(level, index) in sortedVehicleLevels" :key="level">
                                    <div class="bg-blue-50 border border-blue-200 text-blue-700 px-3 py-1 rounded-md text-sm font-medium">
                                        {{ getLevelLabel(level) }}
                                    </div>
                                    <ArrowRightOutlined v-if="index < sortedVehicleLevels.length - 1" class="text-gray-300" />
                                </template>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Block B: Coding Template -->
                <div class="border-t pt-4 mt-4">
                    <h3 class="mb-4 font-bold">SPU 编码模板 (Coding Template)</h3>
                    <Form.Item label="配置模式">
                        <Radio.Group v-model:value="useInheritedTemplate">
                            <Radio :value="true" v-if="parentCategory">继承自父级</Radio>
                            <Radio :value="false">自定义配置</Radio>
                        </Radio.Group>
                    </Form.Item>

                    <div v-if="useInheritedTemplate" class="bg-gray-50 p-3 rounded mb-4 text-gray-500">
                        <InfoCircleOutlined /> 继承模板: <Tag color="blue">{{ effectiveTemplate }}</Tag>
                    </div>

                    <div v-else>
                        <Form.Item label="生成模板" tooltip="点击下方标签添加变量，支持使用箭头排序">
                            <!-- Visual Builder Area -->
                            <div class="border rounded p-3 bg-gray-50 min-h-[40px] flex flex-wrap items-center gap-2 mb-2">
                                <template v-if="templateSegments.length > 0">
                                    <div v-for="(seg, index) in templateSegments" :key="index" class="flex items-center">
                                        <Tag color="blue" class="flex items-center gap-1 m-0">
                                            <span>{{ seg }}</span>
                                            <Space :size="2" class="ml-1">
                                                <ArrowLeftOutlined v-if="index > 0" class="cursor-pointer hover:text-white" @click.stop="moveTemplateSegment(index, -1)" />
                                                <ArrowRightOutlined v-if="index < templateSegments.length - 1" class="cursor-pointer hover:text-white" @click.stop="moveTemplateSegment(index, 1)" />
                                                <CloseOutlined class="cursor-pointer hover:text-red-200 ml-1" @click.stop="removeTemplateSegment(index)" />
                                            </Space>
                                        </Tag>
                                        <!-- Separator -->
                                        <span v-if="index < templateSegments.length - 1" class="text-gray-400 font-bold mx-1">-</span>
                                    </div>
                                </template>
                                <span v-else class="text-gray-400 text-sm">请点击下方按钮构建模板...</span>
                            </div>
                            
                            <!-- Available Variables -->
                            <div class="flex flex-wrap gap-2 mb-4">
                                <!-- Vehicle Vars Group -->
                                <div class="flex items-center gap-2 border-r pr-2 mr-2">
                                    <span class="text-xs text-gray-400">车型变量:</span>
                                    <Tag 
                                        v-for="v in availableVars.filter(i => vehicleVars.includes(i.value))" 
                                        :key="v.value" 
                                        :color="v.color" 
                                        class="cursor-pointer hover:opacity-80 select-none"
                                        @click="addTemplateSegment(v.value)"
                                    >
                                        <PlusOutlined /> {{ v.label }}
                                    </Tag>
                                </div>
                                
                                <!-- General Vars Group -->
                                <div class="flex items-center gap-2">
                                    <span class="text-xs text-gray-400">通用变量:</span>
                                    <Tag 
                                        v-for="v in availableVars.filter(i => !vehicleVars.includes(i.value))" 
                                        :key="v.value" 
                                        :color="v.color" 
                                        class="cursor-pointer hover:opacity-80 select-none"
                                        @click="addTemplateSegment(v.value)"
                                    >
                                        <PlusOutlined /> {{ v.label }}
                                    </Tag>
                                </div>
                            </div>

                            <!-- Live Preview -->
                            <div class="bg-blue-50 border border-blue-100 rounded p-3 flex items-center justify-between">
                                <div>
                                    <div class="text-xs text-blue-500 font-bold mb-1 uppercase">SPU Preview</div>
                                    <div class="text-lg font-mono text-gray-800 font-bold">
                                        {{ previewSku || '等待配置...' }}
                                    </div>
                                </div>
                                <Button size="small" type="text" @click="refreshSkuPreview">
                                    <template #icon><component :is="isPreviewLoading ? 'LoadingOutlined' : 'ReloadOutlined'" /></template>
                                    刷新示例
                                </Button>
                            </div>
                        </Form.Item>
                    </div>
                </div>
            </Form>
          </Tabs.TabPane>
          
          <!-- TAB 3: Attributes -->
          <Tabs.TabPane key="attributes" tab="规格属性" :disabled="!isEditMode">
            <div class="pt-4">
                <!-- Part A: Inherited Attributes (Read-only) -->
                <div class="mb-6" v-if="inheritedAttributes.length > 0">
                    <div class="mb-2 flex items-center gap-2 text-gray-500 font-medium text-sm">
                        <InfoCircleOutlined /> 继承的属性 (Inherited)
                    </div>
                    <div class="bg-gray-50 rounded border border-gray-100 p-2">
                        <Table
                            :columns="[
                                { title: '属性名称', dataIndex: 'label', width: '30%' },
                                { title: 'Key', dataIndex: 'key', width: '30%' },
                                { title: '来源', dataIndex: 'origin_category_name', width: '40%' }
                            ]"
                            :data-source="inheritedAttributes"
                            size="small"
                            :pagination="false"
                            :showHeader="false"
                        >
                            <template #bodyCell="{ column, record }">
                                <template v-if="column.dataIndex === 'label'">
                                    <span class="text-gray-600">{{ record.label }}</span>
                                    <Tag v-if="record.data_type" class="ml-2 text-xs text-gray-400">{{ record.data_type }}</Tag>
                                </template>
                                <template v-if="column.dataIndex === 'origin_category_name'">
                                    <Tag color="blue">来自: {{ record.origin_category_name }}</Tag>
                                </template>
                            </template>
                        </Table>
                    </div>
                </div>

                <!-- Part B: Self Attributes (Editable) -->
                <div>
                    <div class="mb-2 font-bold text-gray-700 flex justify-between items-center">
                        <span>当前分类属性配置</span>
                        
                        <!-- Copy Config Action -->
                        <div class="flex items-center gap-2">
                            <Cascader 
                                v-model:value="copySourceId" 
                                :options="copyOptions" 
                                placeholder="从其他分类复制配置..." 
                                size="small"
                                style="width: 200px"
                                :show-search="{ filter: (inputValue, path) => path.some(option => option.label.toLowerCase().indexOf(inputValue.toLowerCase()) > -1) }"
                                expand-trigger="hover"
                            />
                            <Button 
                                type="dashed" 
                                size="small" 
                                :disabled="copySourceId.length === 0" 
                                :loading="copyLoading"
                                @click="handleCopyConfig"
                            >
                                复制
                            </Button>
                        </div>
                    </div>
                    
                    <div class="mb-4 bg-blue-50 p-4 rounded border border-blue-100">
                        <div class="flex items-center gap-4">
                            <Select 
                                v-model:value="newAttrForm.attribute_id" 
                                placeholder="选择属性定义"
                                style="width: 200px"
                                show-search
                                :options="attributeOptions"
                                :filter-option="(input, option) => (option?.label ?? '').toLowerCase().includes(input.toLowerCase())"
                            />
                            <Select 
                                v-model:value="newAttrForm.group_name" 
                                placeholder="属性分组 (可选)" 
                                style="width: 150px" 
                                :options="groupDictOptions"
                                allow-clear
                            />
                            <Switch v-model:checked="newAttrForm.is_required" checked-children="必填" un-checked-children="非必填" />
                            <Button type="primary" :loading="addingAttr" :disabled="!newAttrForm.attribute_id" @click="handleAddAttribute">
                                <PlusOutlined /> 添加
                            </Button>
                        </div>
                    </div>

                    <!-- Grouped Tables -->
                    <div v-if="selfAttributes.length === 0" class="text-center text-gray-400 py-4 border border-dashed rounded mt-2">
                        暂无自定义属性
                    </div>
                    
                    <template v-else>
                        <div v-for="gName in groupNames" :key="gName" class="mb-4">
                            <div class="flex items-center gap-2 mb-2 pl-2 border-l-4 border-blue-400 bg-gray-50 py-1">
                                <span class="font-bold text-gray-700">{{ gName }}</span>
                                <span class="text-xs text-gray-400 bg-white px-1 rounded border">{{ (groupedSelfAttributes[gName] || []).length }}</span>
                            </div>
                            
                            <Table
                                :columns="selfAttributeColumns"
                                :data-source="groupedSelfAttributes[gName]"
                                :loading="attrLoading"
                                row-key="key" 
                                size="small"
                                :pagination="false"
                                bordered
                            >
                                <template #bodyCell="{ column, record }">
                                    <template v-if="column.key === 'label'">
                                        <div class="flex items-center group/label">
                                            <span class="font-medium text-blue-700 mr-2">{{ record.label }}</span>
                                            <Tag v-if="record.data_type" class="mr-2">{{ record.data_type }}</Tag>
                                            
                                            <!-- Quick Group Edit Popover -->
                                            <Popover title="修改分组" trigger="click">
                                                <template #content>
                                                    <div class="flex gap-2">
                                            <Select 
                                                v-model:value="record._tempGroupName" 
                                                :placeholder="record.group_name || '默认分组'" 
                                                size="small"
                                                style="width: 140px"
                                                :options="groupDictOptions"
                                            />
                                                        <Button 
                                                            type="primary" 
                                                            size="small" 
                                                            @click="handleUpdateGroup(record, record._tempGroupName)"
                                                        >
                                                            保存
                                                        </Button>
                                                    </div>
                                                </template>
                                                <EditOutlined class="text-gray-300 hover:text-blue-500 cursor-pointer opacity-0 group-hover/label:opacity-100 transition-opacity" />
                                            </Popover>
                                        </div>
                                    </template>
                                    
                                    <template v-if="column.key === 'is_required'">
                                        <Switch 
                                            :checked="record.is_required" 
                                            size="small"
                                            @change="(checked: any) => handleToggleRequired(record, !!checked)"
                                        />
                                    </template>

                                    <template v-if="column.key === 'include_in_code'">
                                        <Switch 
                                            :checked="record.include_in_code ?? false" 
                                            size="small"
                                            checked-children="是"
                                            un-checked-children="否"
                                            @change="(checked: any) => handleToggleIncludeCode(record, !!checked)"
                                        />
                                    </template>

                                    <template v-if="column.key === 'options'">
                                        <div class="flex items-start gap-2 group cursor-pointer min-h-[24px]" @click="handleConfigOptions(record)" title="点击配置选项">
                                            <div class="flex-1">
                                                <div class="flex flex-wrap gap-1 items-center">
                                                    <!-- Mode Badge -->
                                                    <Tag v-if="record.override_options === null" color="default" class="mr-1 text-xs px-1 font-normal scale-90 origin-left">全局</Tag>
                                                    <Tag v-else color="blue" class="mr-1 text-xs px-1 font-normal scale-90 origin-left">自定义</Tag>

                                                    <!-- Options Preview -->
                                                    <template v-if="(record.effective_options || []).length > 0">
                                                        <Tag 
                                                            v-for="(opt, idx) in (record.effective_options || []).slice(0, 4)" 
                                                            :key="idx" 
                                                            class="mr-0 max-w-[80px] overflow-hidden text-ellipsis whitespace-nowrap" 
                                                            :color="record.override_options !== null ? 'blue' : undefined"
                                                            size="small"
                                                        >
                                                            {{ typeof opt === 'object' ? opt.label : opt }}
                                                        </Tag>
                                                        <Tag v-if="(record.effective_options || []).length > 4" class="mr-0 text-gray-400 bg-gray-50 border-gray-200">
                                                            +{{ (record.effective_options || []).length - 4 }}
                                                        </Tag>
                                                    </template>
                                                    <span v-else class="text-gray-300 text-xs italic">无选项</span>
                                                </div>
                                            </div>
                                            <EditOutlined class="text-blue-500 opacity-0 group-hover:opacity-100 mt-1 transition-opacity" />
                                        </div>
                                    </template>
                                    
                                    <template v-if="column.key === 'action'">
                                            <Button 
                                                type="link" 
                                                danger 
                                                size="small" 
                                                @click="handleRemoveAttribute(record)"
                                            >
                                                移除
                                            </Button>
                                        </template>
                                    </template>
                            </Table>
                        </div>
                    </template>
                </div>
            </div>
          </Tabs.TabPane>
        </Tabs>
      </Modal>

      <!-- Options Configuration Modal -->
      <Modal
        v-model:open="optionsModalVisible"
        title="配置属性选项"
        @ok="handleSaveOptions"
        width="600px"
      >
        <div v-if="currentEditAttr">
            <div class="mb-4">
                <div class="font-bold text-lg mb-1">{{ currentEditAttr.label }} ({{ currentEditAttr.key_name || currentEditAttr.key }})</div>
                <div class="text-gray-400 text-sm">配置该分类下此属性的可选值集合。</div>
            </div>

            <Form layout="vertical">
                <Form.Item label="配置模式">
                    <Radio.Group v-model:value="useGlobalOptions">
                        <Radio :value="true">使用全局通用选项</Radio>
                        <Radio :value="false">自定义选项 (覆盖)</Radio>
                    </Radio.Group>
                </Form.Item>

                <div v-if="useGlobalOptions" class="bg-gray-50 p-4 rounded border">
                    <div class="text-gray-500 mb-2"><InfoCircleOutlined /> 当前使用的是全局定义的标准选项：</div>
                    <div class="flex flex-wrap gap-2">
                        <Tag v-for="(opt, idx) in editingOptions" :key="idx">
                            {{ typeof opt === 'object' ? opt.label : opt }}
                        </Tag>
                        <span v-if="editingOptions.length === 0" class="text-gray-400 italic">无选项</span>
                    </div>
                </div>

                <div v-else class="bg-blue-50 p-4 rounded border border-blue-100">
                    <div class="text-blue-700 font-medium mb-2">自定义选项列表 (仅对当前分类有效)</div>
                    
                    <!-- Add Input -->
                    <div class="flex gap-2 mb-4">
                        <Input v-model:value="newOptionItem.value" placeholder="选项值 (Value)" style="width: 40%" />
                        <Input v-model:value="newOptionItem.label" placeholder="显示名 (Label, 可选)" style="width: 40%" />
                        <Button type="primary" @click="handleAddOption" :disabled="!newOptionItem.value">
                            <PlusOutlined /> 添加
                        </Button>
                    </div>

                    <!-- List -->
                    <div class="max-h-[300px] overflow-y-auto border rounded bg-white">
                        <Table
                            :columns="[
                                { title: '显示名', dataIndex: 'label', width: '40%' },
                                { title: '值', dataIndex: 'value', width: '40%' },
                                { title: '操作', key: 'action' }
                            ]"
                            :data-source="editingOptions.map(o => typeof o === 'object' ? o : { label: o, value: o })"
                            size="small"
                            :pagination="false"
                        >
                            <template #bodyCell="{ column, record, index }">
                                <template v-if="column.key === 'action'">
                                    <Button type="link" danger size="small" @click="handleRemoveOption(index)">删除</Button>
                                </template>
                            </template>
                        </Table>
                    </div>
                </div>
            </Form>
        </div>
      </Modal>

    </div>
  </Page>
</template>

