<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Button, message, Space, Popconfirm, Tag } from 'ant-design-vue';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons-vue';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getOverseasConsigneeList, createOverseasConsignee, type OverseasConsignee } from '#/api/customs/consignee';
import ConsigneeModal from './ConsigneeModal.vue';

// --- Grid Config ---
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 60 },
    { field: 'name', title: '名称', minWidth: 200 },
    { field: 'country', title: '国家/地区', width: 120 },
    { field: 'contact_info', title: '联系方式', width: 150 },
    { field: 'address', title: '地址', minWidth: 200 },
    { field: 'is_active', title: '状态', width: 80, slots: { default: 'active' } },
    { title: '操作', width: 140, slots: { default: 'action' }, fixed: 'right' }
  ],
  data: [],
  pagerConfig: {
    enabled: false
  },
  toolbarConfig: {
    custom: true
  },
  height: 'auto'
};

const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions,
});

// --- State ---
const modalVisible = ref(false);
const editingRecord = ref<OverseasConsignee | null>(null);

// --- Actions ---
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getOverseasConsigneeList();
    gridApi.setGridOptions({ data: res });
  } catch (e) {
    console.error(e);
  } finally {
    gridApi.setLoading(false);
  }
}

function handleAdd() {
  editingRecord.value = null;
  modalVisible.value = true;
}

function handleEdit(record: OverseasConsignee) {
  editingRecord.value = { ...record };
  modalVisible.value = true;
}

// TODO: Implement Delete API if needed
async function handleDelete(record: OverseasConsignee) {
    message.warning('删除功能暂未开放');
}

function handleModalSuccess() {
  modalVisible.value = false;
  loadData();
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <Page title="境外收货人管理">
    <template #extra>
      <Button type="primary" @click="handleAdd">
        <PlusOutlined /> 新建收货人
      </Button>
    </template>
    
    <div class="p-4">
      <Grid>
        <template #active="{ row }">
          <Tag v-if="row.is_active" color="success">启用</Tag>
          <Tag v-else color="error">禁用</Tag>
        </template>
        
        <template #action="{ row }">
          <Space>
            <Button type="link" size="small" @click="handleEdit(row)">
              <EditOutlined /> 编辑
            </Button>
            <Popconfirm title="确认删除?" @confirm="handleDelete(row)">
              <Button type="link" danger size="small">
                <DeleteOutlined /> 删除
              </Button>
            </Popconfirm>
          </Space>
        </template>
      </Grid>
    </div>

    <ConsigneeModal 
      v-model:open="modalVisible"
      :record="editingRecord"
      @success="handleModalSuccess"
    />
  </Page>
</template>

