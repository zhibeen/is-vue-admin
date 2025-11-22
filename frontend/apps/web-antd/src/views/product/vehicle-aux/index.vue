<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import { Page } from '@vben/common-ui';
import { Card, Table, Button, Modal, Form, Input, message, Row, Col, List, Tag, Empty, Popconfirm, Space } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined, CarOutlined } from '@ant-design/icons-vue';
import { 
  getBrandsApi, createBrandApi, updateBrandApi, deleteBrandApi,
  getModelsApi, createModelApi, updateModelApi, deleteModelApi,
  getSubmodelsApi, createSubmodelApi, updateSubmodelApi, deleteSubmodelApi,
  type Brand, type Model, type Submodel
} from '#/api/core/vehicle';

// --- State ---
const brands = ref<Brand[]>([]);
const models = ref<Model[]>([]);
const submodels = ref<Submodel[]>([]);

const selectedBrandId = ref<number | undefined>();
const selectedModelId = ref<number | undefined>();

const loadingBrands = ref(false);
const loadingModels = ref(false);
const loadingSubmodels = ref(false);

// --- Brand Form ---
const brandModalVisible = ref(false);
const brandFormRef = ref();
const brandFormState = ref({ id: undefined as number | undefined, name: '', code: '', abbr: '' });
const isBrandEdit = ref(false);

// --- Model Form ---
const modelModalVisible = ref(false);
const modelFormRef = ref();
const modelFormState = ref({ id: undefined as number | undefined, name: '' });
const isModelEdit = ref(false);

// --- Submodel Form ---
const submodelModalVisible = ref(false);
const submodelFormRef = ref();
const submodelFormState = ref({ id: undefined as number | undefined, name: '' });
const isSubmodelEdit = ref(false);

// --- Lifecycle ---
onMounted(() => {
  loadBrands();
});

async function loadBrands() {
  loadingBrands.value = true;
  try {
    brands.value = await getBrandsApi();
    if (brands.value.length > 0 && !selectedBrandId.value) {
        // Default select first if none selected
        // handleSelectBrand(brands.value[0].id); 
    }
  } catch (error) {
    console.error(error);
  } finally {
    loadingBrands.value = false;
  }
}

// --- Computed Data ---
// No longer computed from local array, fetched from API on selection
// But we can use local state for current view

const selectedBrandName = computed(() => {
    return brands.value.find(b => b.id === selectedBrandId.value)?.name || '';
});

const selectedModelName = computed(() => {
    return models.value.find(m => m.id === selectedModelId.value)?.name || '';
});

// --- Navigation Actions ---
async function handleSelectBrand(id: number) {
    if (selectedBrandId.value === id) return;
    selectedBrandId.value = id;
    selectedModelId.value = undefined; // Reset model selection
    submodels.value = []; // Clear submodels
    
    loadingModels.value = true;
    try {
        models.value = await getModelsApi(id);
    } catch (e) {
        console.error(e);
    } finally {
        loadingModels.value = false;
    }
}

async function handleSelectModel(id: number) {
    if (selectedModelId.value === id) return;
    selectedModelId.value = id;
    
    loadingSubmodels.value = true;
    try {
        submodels.value = await getSubmodelsApi(id);
    } catch (e) {
        console.error(e);
    } finally {
        loadingSubmodels.value = false;
    }
}

// --- Brand CRUD ---
function handleAddBrand() {
    isBrandEdit.value = false;
    brandFormState.value = { id: undefined, name: '', code: '', abbr: '' };
    brandModalVisible.value = true;
}

function handleEditBrand(brand: Brand, e: Event) {
    e.stopPropagation();
    isBrandEdit.value = true;
    brandFormState.value = { ...brand };
    brandModalVisible.value = true;
}

async function handleDeleteBrand(id: number, e: Event) {
    e.stopPropagation();
    try {
        await deleteBrandApi(id);
        message.success('删除品牌成功');
        await loadBrands();
        if (selectedBrandId.value === id) {
            selectedBrandId.value = undefined;
            models.value = [];
            submodels.value = [];
        }
    } catch (error) {
        console.error(error);
    }
}

function handleSaveBrand() {
    brandFormRef.value.validate().then(async () => {
        try {
            if (isBrandEdit.value && brandFormState.value.id) {
                await updateBrandApi(brandFormState.value.id, brandFormState.value);
                message.success('更新成功');
            } else {
                await createBrandApi(brandFormState.value as any);
                message.success('创建成功');
            }
            brandModalVisible.value = false;
            await loadBrands();
        } catch (error) {
            console.error(error);
        }
    });
}

// --- Model CRUD ---
function handleAddModel() {
    if (!selectedBrandId.value) return;
    isModelEdit.value = false;
    modelFormState.value = { id: undefined, name: '' };
    modelModalVisible.value = true;
}

function handleEditModel(model: Model) {
    isModelEdit.value = true;
    modelFormState.value = { id: model.id, name: model.name };
    modelModalVisible.value = true;
}

async function handleDeleteModel(id: number) {
    try {
        await deleteModelApi(id);
        message.success('删除车型成功');
        if (selectedBrandId.value) {
            models.value = await getModelsApi(selectedBrandId.value);
        }
        if (selectedModelId.value === id) {
            selectedModelId.value = undefined;
            submodels.value = [];
        }
    } catch (error) {
        console.error(error);
    }
}

function handleSaveModel() {
    modelFormRef.value.validate().then(async () => {
        try {
            if (isModelEdit.value && modelFormState.value.id) {
                await updateModelApi(modelFormState.value.id, { name: modelFormState.value.name });
                message.success('更新成功');
            } else {
                if (!selectedBrandId.value) return;
                await createModelApi({
                    brand_id: selectedBrandId.value,
                    name: modelFormState.value.name
                });
                message.success('创建成功');
            }
            modelModalVisible.value = false;
            if (selectedBrandId.value) {
                models.value = await getModelsApi(selectedBrandId.value);
            }
        } catch (error) {
            console.error(error);
        }
    });
}

// --- Submodel CRUD ---
function handleAddSubmodel() {
    isSubmodelEdit.value = false;
    submodelFormState.value = { id: undefined, name: '' };
    submodelModalVisible.value = true;
}

function handleEditSubmodel(submodel: Submodel) {
    isSubmodelEdit.value = true;
    submodelFormState.value = { ...submodel };
    submodelModalVisible.value = true;
}

async function handleDeleteSubmodel(id: number) {
    try {
        await deleteSubmodelApi(id);
        message.success('删除子车型成功');
        if (selectedModelId.value) {
            submodels.value = await getSubmodelsApi(selectedModelId.value);
        }
    } catch (error) {
        console.error(error);
    }
}

function handleSaveSubmodel() {
    submodelFormRef.value.validate().then(async () => {
        try {
            if (isSubmodelEdit.value && submodelFormState.value.id) {
                await updateSubmodelApi(submodelFormState.value.id, { name: submodelFormState.value.name });
                message.success('更新成功');
            } else {
                if (!selectedModelId.value) return;
                await createSubmodelApi({
                    model_id: selectedModelId.value,
                    name: submodelFormState.value.name
                });
                message.success('创建成功');
            }
            submodelModalVisible.value = false;
            if (selectedModelId.value) {
                submodels.value = await getSubmodelsApi(selectedModelId.value);
            }
        } catch (error) {
            console.error(error);
        }
    });
}

const modelColumns = [
    { title: '车型名称 (Model)', dataIndex: 'name', key: 'name' },
    { title: '操作', key: 'action', width: '120px' },
];

const submodelColumns = [
    { title: '子车型名称 (Submodel)', dataIndex: 'name', key: 'name' },
    { title: '操作', key: 'action', width: '150px' },
];

// Custom row for selection styling and interaction
const customModelRow = (record: Model) => {
  const isSelected = selectedModelId.value === record.id;
  return {
    onClick: () => handleSelectModel(record.id),
    class: {
      'bg-orange-100 dark:bg-orange-900/60': isSelected, // 选中背景
      'font-medium': isSelected,   // 选中加粗
      'hover:bg-orange-50 dark:hover:bg-orange-900/30': !isSelected, // Hover
      'cursor-pointer': true,
      'transition-colors': true
    }
  };
};
</script>

<template>
  <Page title="车型辅助目录">
    <div class="p-4 h-full">
        <Row :gutter="16" class="h-full">
            <!-- Left: Brands List (Level 1) -->
            <Col :span="8" class="h-full">
                <Card title="1. 汽车品牌 (Make)" class="h-full flex flex-col" :bodyStyle="{ flex: 1, overflow: 'hidden', padding: '12px' }">
                    <template #extra>
                        <Button type="primary" size="small" @click="handleAddBrand">
                            <PlusOutlined /> 新增
                        </Button>
                    </template>
                    <div class="overflow-y-auto h-[calc(100vh-250px)] pr-2">
                        <List item-layout="horizontal" :data-source="brands" :loading="loadingBrands">
                            <template #renderItem="{ item }">
                                <List.Item 
                                    class="cursor-pointer hover:bg-orange-50 dark:hover:bg-orange-900/30 rounded px-2 transition-colors border-b border-gray-100 dark:border-gray-800"
                                    :class="{ 'bg-orange-100 dark:bg-orange-900/60': selectedBrandId === item.id }"
                                    @click="handleSelectBrand(item.id)"
                                >
                                    <template #actions>
                                        <Button type="link" size="small" @click="(e) => handleEditBrand(item, e)"><EditOutlined /></Button>
                                        <Popconfirm title="确定删除？" @confirm="(e) => handleDeleteBrand(item.id, e)" @click.stop>
                                            <Button type="link" size="small" danger><DeleteOutlined /></Button>
                                        </Popconfirm>
                                    </template>
                                    <List.Item.Meta>
                                        <template #title>
                                            <div class="flex items-center justify-between" :class="{'font-bold': selectedBrandId === item.id}">
                                                <span class="font-medium dark:text-white">{{ item.name }}</span>
                                            </div>
                                        </template>
                                        <template #description>
                                            <div class="flex items-center gap-2 mt-1">
                                                <Tag :color="selectedBrandId === item.id ? 'orange' : 'blue'" class="mr-0 text-[10px] leading-tight px-1">{{ item.code }}</Tag>
                                                <Tag :color="selectedBrandId === item.id ? 'gold' : 'cyan'" class="mr-0 text-[10px] leading-tight px-1">{{ item.abbr }}</Tag>
                                            </div>
                                        </template>
                                        <template #avatar>
                                            <div class="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-500 dark:text-gray-300" :class="{'bg-orange-300 text-black dark:bg-orange-700 dark:text-white': selectedBrandId === item.id}"><CarOutlined /></div>
                                        </template>
                                    </List.Item.Meta>
                                </List.Item>
                            </template>
                        </List>
                    </div>
                </Card>
            </Col>

            <!-- Middle: Model List (Level 2) -->
            <Col :span="8" class="h-full">
                <Card class="h-full flex flex-col" :bodyStyle="{ flex: 1, overflow: 'hidden', padding: '0' }">
                    <template #title>
                        <div class="flex items-center">
                            <span>2. 车型列表 (Model)</span>
                            <span class="mx-2 text-gray-400" v-if="selectedBrandId">|</span>
                            <span class="text-sm font-normal text-gray-500" v-if="selectedBrandId">
                                {{ selectedBrandName }}
                            </span>
                        </div>
                    </template>
                    
                    <template #extra>
                        <Button type="primary" size="small" :disabled="!selectedBrandId" @click="handleAddModel">
                            <PlusOutlined /> 新增车型
                        </Button>
                    </template>

                    <!-- Empty State -->
                    <div v-if="!selectedBrandId" class="flex items-center justify-center h-64 text-gray-400">
                        <Empty description="请先在左侧选择一个品牌" />
                    </div>

                    <!-- Level 2: Models Table -->
                    <div v-else class="p-4 h-full overflow-y-auto">
                        <Table :columns="modelColumns" :data-source="models" :loading="loadingModels" row-key="id" :pagination="{ pageSize: 10 }" size="middle" :customRow="customModelRow">
                            <template #bodyCell="{ column, record }">
                                <template v-if="column.key === 'name'">
                                    <span class="font-medium">{{ record.name }}</span>
                                </template>
                                <template v-if="column.key === 'action'">
                                    <Space>
                                        <Button type="link" size="small" @click.stop="handleEditModel(record)"><EditOutlined /></Button>
                                        <Popconfirm title="删除车型会连带删除子车型，确定？" @confirm="handleDeleteModel(record.id)" @click.stop>
                                            <Button type="link" size="small" danger><DeleteOutlined /></Button>
                                        </Popconfirm>
                                    </Space>
                                </template>
                            </template>
                        </Table>
                    </div>
                </Card>
            </Col>

            <!-- Right: Submodel List (Level 3) -->
             <Col :span="8" class="h-full">
                <Card class="h-full flex flex-col" :bodyStyle="{ flex: 1, overflow: 'hidden', padding: '0' }">
                    <template #title>
                        <div class="flex items-center">
                            <span>3. 子车型列表 (Submodel)</span>
                            <span class="mx-2 text-gray-400" v-if="selectedModelId">|</span>
                            <span class="text-sm font-normal text-gray-500" v-if="selectedModelId">
                                {{ selectedModelName }}
                            </span>
                        </div>
                    </template>
                    
                    <template #extra>
                         <Button type="primary" size="small" :disabled="!selectedModelId" @click="handleAddSubmodel">
                            <PlusOutlined /> 新增子车型
                        </Button>
                    </template>

                    <!-- Empty State -->
                    <div v-if="!selectedModelId" class="flex items-center justify-center h-64 text-gray-400">
                        <Empty description="请先在中间选择一个车型" />
                    </div>

                    <!-- Level 3: Submodels Table -->
                    <div v-else class="p-4 h-full overflow-y-auto">
                        <Table :columns="submodelColumns" :data-source="submodels" :loading="loadingSubmodels" row-key="id" :pagination="{ pageSize: 10 }" size="middle">
                            <template #bodyCell="{ column, record }">
                                <template v-if="column.key === 'action'">
                                    <Space>
                                        <Button type="link" size="small" @click="handleEditSubmodel(record)"><EditOutlined /> 编辑</Button>
                                        <Popconfirm title="确定删除？" @confirm="handleDeleteSubmodel(record.id)">
                                            <Button type="link" size="small" danger><DeleteOutlined /> 删除</Button>
                                        </Popconfirm>
                                    </Space>
                                </template>
                            </template>
                        </Table>
                    </div>
                </Card>
            </Col>
        </Row>

        <!-- Modals -->
        <Modal v-model:open="brandModalVisible" :title="isBrandEdit ? '编辑品牌' : '新增品牌'" @ok="handleSaveBrand">
            <Form ref="brandFormRef" :model="brandFormState" layout="vertical" class="pt-4">
                <Form.Item label="品牌名称" name="name" :rules="[{ required: true, message: '必填' }]"><Input v-model:value="brandFormState.name" /></Form.Item>
                <Row :gutter="16">
                    <Col :span="12">
                         <Form.Item label="数字编码 (2位)" name="code" :rules="[{ required: true, pattern: /^\d{2}$/, message: '2位数字' }]"><Input v-model:value="brandFormState.code" :maxlength="2" /></Form.Item>
                    </Col>
                    <Col :span="12">
                        <Form.Item label="缩写编码" name="abbr" :rules="[{ required: true, message: '必填' }]"><Input v-model:value="brandFormState.abbr" placeholder="如: BMW" /></Form.Item>
                    </Col>
                </Row>
            </Form>
        </Modal>

        <Modal v-model:open="modelModalVisible" :title="isModelEdit ? '编辑车型' : '新增车型'" @ok="handleSaveModel">
            <Form ref="modelFormRef" :model="modelFormState" layout="vertical" class="pt-4">
                <Form.Item label="车型名称" name="name" :rules="[{ required: true, message: '必填' }]"><Input v-model:value="modelFormState.name" /></Form.Item>
            </Form>
        </Modal>

        <Modal v-model:open="submodelModalVisible" :title="isSubmodelEdit ? '编辑子车型' : '新增子车型'" @ok="handleSaveSubmodel">
            <Form ref="submodelFormRef" :model="submodelFormState" layout="vertical" class="pt-4">
                <Form.Item label="子车型名称" name="name" :rules="[{ required: true, message: '必填' }]"><Input v-model:value="submodelFormState.name" placeholder="例如：320i M运动型" /></Form.Item>
            </Form>
        </Modal>
    </div>
  </Page>
</template>
