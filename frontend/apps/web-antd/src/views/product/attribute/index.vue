<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Button, message, Popconfirm, Tag, Space, Typography } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined, AppstoreOutlined } from '@ant-design/icons-vue';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';

import { 
    getAttributeDefinitionsApi, 
    deleteAttributeDefinitionApi, 
    getDictItemsApi,
    type CategoryAttribute 
} from '#/api/core/product';

import AttributeDrawer from './components/AttributeDrawer.vue';

const { Text } = Typography;

// --- NEW: 类型映射字典 ---
const typeMap: Record<string, { label: string; color: string }> = {
    text: { label: '单行文本', color: 'blue' },
    textarea: { label: '多行文本', color: 'cyan' },
    number: { label: '数字数值', color: 'purple' },
    boolean: { label: '布尔开关', color: 'pink' },
    select: { label: '下拉选项', color: 'orange' },
};

// --- Components Refs ---
const drawerRef = ref();

// --- State ---
const groupOptions = ref<{ label: string; value: string }[]>([]);

// --- Grid Config ---
const gridOptions: VxeGridProps = {
    keepSource: true,
    // height: 'auto', // 移除 auto 以配合 Page 的 auto-content-height
    pagerConfig: {
        enabled: true,
        pageSize: 20,
        pageSizes: [10, 20, 50, 100],
    },
    toolbarConfig: {
        custom: true,
        export: true,
        refresh: true,
        zoom: true,
    },
    proxyConfig: {
        ajax: {
            query: async ({ page }) => {
                const allData = await loadGridData();
                // 前端分页逻辑：模拟后端分页返回
                const { currentPage, pageSize } = page;
                const startIndex = (currentPage - 1) * pageSize;
                const endIndex = startIndex + pageSize;
                const sliceData = allData.slice(startIndex, endIndex);
                return { items: sliceData, total: allData.length };
            }
        }
    },
    columns: [
        { field: 'id', title: 'ID', width: 60, align: 'center' },
        { field: 'label', title: '属性名称', minWidth: 150 },
        { field: 'name_en', title: '英文名称', minWidth: 150, slots: { default: 'name_en_default' } },
        { field: 'key', title: 'Key', width: 180, slots: { default: 'key_default' } },
        { field: 'type', title: '类型', width: 100, align: 'center', slots: { default: 'type_default' } },
        { field: 'group_name', title: '分组', width: 120, slots: { default: 'group_default' } },
        { field: 'options', title: '预设选项', minWidth: 200, slots: { default: 'options_default' } },
        { field: 'code_weight', title: '排序', width: 80, align: 'center', sortable: true },
        { title: '操作', width: 150, fixed: 'right', slots: { default: 'action_default' }, align: 'center' }
    ],
    customConfig: {
        storage: true
    }
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

// --- Methods ---

async function loadGridData() {
    try {
        const res = await getAttributeDefinitionsApi();
        // 兼容处理
        const data = Array.isArray(res) ? res : (res as any).data || [];
        return data;
    } catch (e) {
        console.error(e);
        return [];
    }
}

async function loadGroupDicts() {
    try {
        const res = await getDictItemsApi('product_attribute_group');
        const items = Array.isArray(res) ? res : (res as any).data || [];
        groupOptions.value = items.map((item: any) => ({
            label: item.label,
            value: item.value
        }));
    } catch (e) {
        // Silent fail or default
    }
}

function handleAdd() {
    drawerRef.value?.open();
}

function handleEdit(record: CategoryAttribute) {
    drawerRef.value?.open(record);
}

async function handleDelete(id: string) {
    try {
        await deleteAttributeDefinitionApi(id);
        message.success('删除成功');
        gridApi.query(); // 刷新表格
    } catch (e) {
        // Error handled in interceptor usually, but nice to have fallback
    }
}

// function getTypeColor(type: string) {
//     const map: Record<string, string> = {
//         text: 'blue',
//         number: 'cyan',
//         boolean: 'purple',
//         select: 'orange',
//         textarea: 'geekblue'
//     };
//     return map[type] || 'default';
// }

function handleGroupUpdate(newGroup: { label: string, value: string }) {
    // 乐观更新，实际应该调用 API 保存字典
    groupOptions.value.push(newGroup);
}

onMounted(() => {
    loadGroupDicts();
});
</script>

<template>
  <Page title="商品属性库管理" auto-content-height>
    <template #extra>
        <Space>
            <Button type="primary" @click="handleAdd">
                <PlusOutlined /> 新增属性
            </Button>
            <Button href="/system/dict" target="_blank">
                <AppstoreOutlined /> 分组管理
            </Button>
        </Space>
    </template>

    <div class="p-4 h-full">
        <Grid class="h-full">
             <!-- EN Name Slot -->
             <template #name_en_default="{ row }">
                 <span v-if="row.name_en" class="text-gray-500">{{ row.name_en }}</span>
                 <span v-else class="text-gray-300">-</span>
             </template>

             <!-- Key Slot -->
             <template #key_default="{ row }">
                 <Text copyable class="text-gray-500">{{ row.key }}</Text>
             </template>

             <!-- Type Slot -->
             <template #type_default="{ row }">
                 <Tag :color="typeMap[row.type]?.color || 'default'">
                    {{ typeMap[row.type]?.label || row.type }}
                 </Tag>
             </template>

             <!-- Group Slot -->
             <template #group_default="{ row }">
                <Tag v-if="row.group_name" color="blue">
                    {{ groupOptions.find(o => o.value === row.group_name)?.label || row.group_name }}
                </Tag>
                <span v-else class="text-gray-300">-</span>
             </template>

             <!-- Options Slot -->
             <template #options_default="{ row }">
                <template v-if="row.type === 'select' && row.options?.length">
                    <div class="flex flex-wrap gap-1">
                        <Tag v-for="(opt, idx) in row.options.slice(0, 3)" :key="idx" size="small" :bordered="false">
                             {{ typeof opt === 'object' ? opt.label : opt }}
                        </Tag>
                         <Tag v-if="row.options.length > 3" size="small" class="bg-gray-100 text-gray-500">
                             +{{ row.options.length - 3 }}
                        </Tag>
                    </div>
                </template>
                <span v-else class="text-gray-300">-</span>
             </template>

             <!-- Action Slot -->
             <template #action_default="{ row }">
                 <Space>
                    <Button type="link" size="small" @click="handleEdit(row)">
                        <EditOutlined /> 编辑
                    </Button>
                    <Popconfirm title="确定删除?" @confirm="handleDelete(row.id)">
                        <Button type="link" size="small" danger>
                             <DeleteOutlined /> 删除
                        </Button>
                    </Popconfirm>
                 </Space>
             </template>
        </Grid>
    </div>

    <AttributeDrawer 
        ref="drawerRef" 
        :group-options="groupOptions"
        @success="gridApi.query()"
        @update:group-options="handleGroupUpdate"
    />
  </Page>
</template>
