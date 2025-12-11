<template>
  <div class="py-4">
    <!-- 顶部工具栏 -->
    <div class="mb-4 flex justify-between items-center">
      <Space>
        <!-- 仓库筛选 (控制 Level 2 vs Level 3) -->
        <Select 
            v-model:value="filterWarehouseId" 
            style="width: 200px" 
            placeholder="选择作用域"
            allowClear
            @change="loadData"
        >
            <SelectOption :value="null">全部仓库 (通用规则)</SelectOption>
            <SelectOption v-for="w in warehouses" :key="w.id" :value="w.id">
                {{ w.name }} ({{ w.code }})
            </SelectOption>
        </Select>

        <InputSearch 
            v-model:value="searchText"
            placeholder="搜索 SKU / 产品名称" 
            style="width: 250px" 
            @search="loadData"
        />
      </Space>
      
      <Space>
        <Button @click="handleSyncProducts" :loading="syncing">同步商品</Button>
        <Button>导入配对</Button>
        <Button type="primary" @click="handleAdd">新增配对</Button>
      </Space>
    </div>

    <!-- 表格 -->
    <Table 
      :columns="columns" 
      :data-source="dataSource" 
      :loading="loading"
      row-key="id"
      size="middle"
      :pagination="{ pageSize: 20 }"
    >
      <template #bodyCell="{ column, record }">
        <!-- 作用域列 -->
        <template v-if="column.key === 'scope'">
            <Tag color="orange" v-if="!record.warehouse_id">通用 (所有仓库)</Tag>
            <Tag color="blue" v-else>{{ record.warehouse_name }}</Tag>
        </template>

        <!-- 远程 SKU -->
        <template v-if="column.key === 'remote'">
            <div>
                <div class="font-bold">{{ record.remote_sku }}</div>
                <div class="text-xs text-gray-400">{{ record.remote_name || '未知三方商品' }}</div>
            </div>
        </template>

        <!-- 本地 SKU -->
        <template v-if="column.key === 'local'">
            <div v-if="record.local_sku" class="flex items-center text-success">
                 <LinkOutlined class="mr-2" />
                 <div>
                    <div class="font-bold">{{ record.local_sku }}</div>
                    <!-- 可以在这里调用 API 获取本地商品名称 -->
                 </div>
            </div>
            <span v-else class="text-gray-400">未配对</span>
        </template>

        <template v-if="column.key === 'action'">
          <Space>
             <Button type="link" size="small" @click="handleEdit(record)">编辑</Button>
             <Popconfirm title="确定解绑吗?" @confirm="handleDelete(record)">
                <Button type="link" danger size="small">解绑</Button>
             </Popconfirm>
          </Space>
        </template>
      </template>
    </Table>

    <!-- 配对弹窗 -->
    <Modal 
        v-model:open="modalVisible" 
        :title="currentRecord ? '编辑配对' : '新增配对'"
        @ok="handleSave"
        :confirmLoading="saving"
    >
        <Form :model="formState" layout="vertical" ref="formRef">
            <FormItem label="作用域 (仓库)">
                 <Select v-model:value="formState.warehouse_id" allowClear placeholder="留空则为通用规则(所有仓库生效)">
                    <SelectOption :value="null">全部仓库 (通用)</SelectOption>
                    <SelectOption v-for="w in warehouses" :key="w.id" :value="w.id">
                        {{ w.name }}
                    </SelectOption>
                 </Select>
                 <div class="text-xs text-gray-500 mt-1">如果不选择仓库，此规则将应用于该服务商下的所有仓库。</div>
            </FormItem>
            <FormItem label="第三方 SKU" required name="remote_sku">
                <!-- 支持搜索和选择已同步的商品 -->
                <Select
                    v-model:value="formState.remote_sku"
                    show-search
                    placeholder="选择或输入第三方 SKU"
                    :options="productOptions"
                    :filter-option="filterOption"
                    allowClear
                />
            </FormItem>
            <FormItem label="本地系统 SKU" required name="local_sku">
                <Input v-model:value="formState.local_sku" placeholder="请输入本地 SKU" />
            </FormItem>
            <FormItem label="数量比例 (1个三方单位 = N个本地单位)">
                <InputNumber v-model:value="formState.quantity_ratio" :min="0.01" :step="1" style="width: 100%" />
            </FormItem>
        </Form>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, watch, computed } from 'vue';
import { Table, Space, Select, SelectOption, Input, InputSearch, Button, Tag, Popconfirm, Modal, Form, FormItem, InputNumber, message } from 'ant-design-vue';
import { LinkOutlined } from '@ant-design/icons-vue';
import { requestClient } from '#/api/request';

const props = defineProps<{ serviceId: number }>();
const loading = ref(false);
const dataSource = ref<any[]>([]);
const searchText = ref('');
const filterWarehouseId = ref<number | null>(null);
const warehouses = ref<any[]>([]);
const syncing = ref(false);
const products = ref<any[]>([]);

// Modal state
const modalVisible = ref(false);
const saving = ref(false);
const currentRecord = ref<any>(null);
const formState = reactive({
    warehouse_id: null as number | null,
    remote_sku: '',
    local_sku: '',
    quantity_ratio: 1.0
});

const columns = [
    { title: '作用域', key: 'scope', width: 150 },
    { title: '三方 SKU', key: 'remote', width: 250 },
    { title: '配对关系', key: 'arrow', width: 50, align: 'center' as const, customRender: () => '➜' },
    { title: '系统 SKU', key: 'local', width: 250 },
    { title: '比例', dataIndex: 'quantity_ratio', width: 80 },
    { title: '操作', key: 'action', width: 150 }
];

// 加载仓库列表（用于筛选）
const loadWarehouses = async () => {
    try {
        const res = await requestClient.get(`/v1/third-party/services/${props.serviceId}/warehouses`);
        warehouses.value = res;
    } catch (e) {
        console.error(e);
    }
};

const loadData = async () => {
    if (!props.serviceId) return;
    loading.value = true;
    try {
        const params: any = {};
        if (filterWarehouseId.value) params.warehouse_id = filterWarehouseId.value;
        if (searchText.value) params.q = searchText.value;
        
        const res = await requestClient.get(`/v1/third-party/services/${props.serviceId}/sku-mappings`, { params });
        dataSource.value = res;
    } finally {
        loading.value = false;
    }
};

// 加载三方商品列表 (用于下拉选择)
const loadProducts = async () => {
    try {
        const res = await requestClient.get(`/v1/third-party/services/${props.serviceId}/products`);
        products.value = res;
    } catch (e) {
        console.error(e);
    }
};

const productOptions = computed(() => {
    return products.value.map(p => ({
        label: `${p.remote_sku} - ${p.remote_name}`,
        value: p.remote_sku
    }));
});

const filterOption = (input: string, option: any) => {
    return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
};

const handleSyncProducts = async () => {
    try {
        syncing.value = true;
        const res = await requestClient.post<{synced_count: number, message: string}>(`/v1/third-party/services/${props.serviceId}/products/sync`);
        message.success(`同步完成，更新了 ${res.synced_count} 个商品`);
        loadProducts(); // 刷新下拉列表
    } catch (e: any) {
        message.error(e.message || '同步失败');
    } finally {
        syncing.value = false;
    }
};

const handleAdd = () => {
    currentRecord.value = null;
    formState.warehouse_id = filterWarehouseId.value; // 默认选中当前筛选的仓库
    formState.remote_sku = '';
    formState.local_sku = '';
    formState.quantity_ratio = 1.0;
    
    // 如果产品列表为空，尝试加载一下
    if (products.value.length === 0) loadProducts();
    
    modalVisible.value = true;
};

const handleEdit = (record: any) => {
    currentRecord.value = record;
    formState.warehouse_id = record.warehouse_id;
    formState.remote_sku = record.remote_sku;
    formState.local_sku = record.local_sku;
    formState.quantity_ratio = record.quantity_ratio;
    
    if (products.value.length === 0) loadProducts();
    
    modalVisible.value = true;
};

const handleSave = async () => {
    if (!formState.remote_sku || !formState.local_sku) {
        message.error('请填写完整的配对信息');
        return;
    }
    
    saving.value = true;
    try {
        await requestClient.post(`/v1/third-party/services/${props.serviceId}/sku-mappings`, formState);
        message.success('保存成功');
        modalVisible.value = false;
        loadData();
    } catch (e: any) {
        message.error(e.message || '保存失败');
    } finally {
        saving.value = false;
    }
};

const handleDelete = async (record: any) => {
    try {
        await requestClient.delete(`/v1/third-party/services/${props.serviceId}/sku-mappings/${record.id}`);
        message.success('解绑成功');
        loadData();
    } catch (e: any) {
        message.error(e.message || '操作失败');
    }
};

watch(() => props.serviceId, () => {
    loadWarehouses();
    loadData();
    // 延迟加载产品列表，避免页面初始化太慢
    setTimeout(loadProducts, 1000);
}, { immediate: true });

onMounted(() => {
    loadWarehouses();
    loadData();
});
</script>
