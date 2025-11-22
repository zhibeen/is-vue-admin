<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Card, Table, Button, Modal, Form, Input, Switch, message, Tree, Space, Tag, Row, Col } from 'ant-design-vue';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';

interface CategoryItem {
  id: string;
  parentId: string | null;
  name: string;
  skuCode: string;      // SKU数字编码 (3位)
  featureCode: string;  // 业务特征码 (字母)
  isLeaf: boolean;
  children?: CategoryItem[];
}

// --- Mock Data ---
const mockData: CategoryItem[] = [
  {
    id: '1',
    parentId: null,
    name: '汽车照明 (Lighting)',
    skuCode: '150', 
    featureCode: 'LGT',
    isLeaf: false,
    children: [
      {
        id: '11',
        parentId: '1',
        name: '前大灯 (Headlight)',
        skuCode: '151',
        featureCode: 'HL',
        isLeaf: true,
      },
      {
        id: '12',
        parentId: '1',
        name: '尾灯 (Tail Light)',
        skuCode: '152',
        featureCode: 'TL',
        isLeaf: true,
      }
    ]
  },
  {
    id: '2',
    parentId: null,
    name: '车身覆盖件 (Body Parts)',
    skuCode: '180',
    featureCode: 'BDY',
    isLeaf: false,
    children: [
      {
        id: '21',
        parentId: '2',
        name: '保险杠 (Bumper)',
        skuCode: '188',
        featureCode: 'BMP',
        isLeaf: true,
      }
    ]
  }
];

// --- State ---
const treeData = ref<CategoryItem[]>([]);
const loading = ref(false);
const modalVisible = ref(false);
const modalTitle = ref('');
const isEditMode = ref(false);

const formRef = ref();
const formState = ref({
  id: '',
  parentId: null as string | null,
  name: '',
  skuCode: '',
  featureCode: '',
  isLeaf: false
});

const columns = [
  { title: '分类名称', dataIndex: 'name', key: 'name', width: '30%' },
  { title: 'SKU编码 (数字)', dataIndex: 'skuCode', key: 'skuCode', width: '20%' },
  { title: '特征码 (字母)', dataIndex: 'featureCode', key: 'featureCode', width: '20%' },
  { title: '类型', key: 'type', width: '10%' },
  { title: '操作', key: 'action', width: '20%' },
];

// --- Lifecycle ---
onMounted(() => {
  loadData();
});

function loadData() {
  loading.value = true;
  // Mock API call
  setTimeout(() => {
    treeData.value = JSON.parse(JSON.stringify(mockData));
    loading.value = false;
  }, 500);
}

// --- Actions ---
function handleAdd(parentId: string | null = null) {
  isEditMode.value = false;
  modalTitle.value = parentId ? '新增子分类' : '新增一级分类';
  formState.value = {
    id: '',
    parentId: parentId,
    name: '',
    skuCode: '',
    featureCode: '',
    isLeaf: !!parentId // Default to leaf if adding child, user can change
  };
  modalVisible.value = true;
}

function handleEdit(record: CategoryItem) {
  isEditMode.value = true;
  modalTitle.value = '编辑分类';
  formState.value = { ...record };
  modalVisible.value = true;
}

function handleDelete(id: string) {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个分类吗？如果是父分类，子分类也会被影响。',
    onOk() {
      message.success('删除成功 (模拟)');
      loadData();
    }
  });
}

function handleSave() {
  formRef.value.validate().then(() => {
    console.log('Saving:', formState.value);
    message.success('保存成功 (模拟)');
    modalVisible.value = false;
    loadData();
  }).catch(() => {
    // validation failed
  });
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
        >
           <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'skuCode'">
                  <Tag color="blue">{{ record.skuCode }}</Tag>
              </template>
              <template v-if="column.key === 'featureCode'">
                  <Tag color="orange">{{ record.featureCode }}</Tag>
              </template>
              <template v-if="column.key === 'type'">
                  <Tag v-if="record.isLeaf" color="green">叶子节点</Tag>
                  <Tag v-else>目录节点</Tag>
              </template>
              <template v-if="column.key === 'action'">
                  <Space>
                      <Button type="link" size="small" @click="handleEdit(record)">
                          <EditOutlined /> 编辑
                      </Button>
                      <Button type="link" size="small" @click="handleAdd(record.id)" v-if="!record.isLeaf">
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
        width="600px"
      >
        <Form
            ref="formRef"
            :model="formState"
            layout="vertical"
            class="pt-4"
        >
            <Form.Item label="分类名称" name="name" :rules="[{ required: true, message: '请输入分类名称' }]">
                <Input v-model:value="formState.name" placeholder="例如：前大灯" />
            </Form.Item>
            
            <Row :gutter="16">
                <Col :span="12">
                    <Form.Item 
                        label="SKU编码 (数字)" 
                        name="skuCode" 
                        :rules="[{ required: true, message: '请输入3位数字编码', pattern: /^\d{3}$/ }]"
                        tooltip="用于生成SKU的3位数字，如 188"
                    >
                        <Input v-model:value="formState.skuCode" placeholder="000-999" :maxlength="3" />
                    </Form.Item>
                </Col>
                <Col :span="12">
                    <Form.Item 
                        label="特征码 (字母)" 
                        name="featureCode" 
                        :rules="[{ required: true, message: '请输入业务特征码' }]"
                        tooltip="用于业务识别的字母缩写，如 HL"
                    >
                        <Input v-model:value="formState.featureCode" placeholder="如 HL" />
                    </Form.Item>
                </Col>
            </Row>
            
            <Form.Item label="节点类型" name="isLeaf" tooltip="叶子节点才能关联具体产品">
                <Switch 
                    v-model:checked="formState.isLeaf" 
                    checked-children="叶子节点" 
                    un-checked-children="目录节点" 
                />
            </Form.Item>
        </Form>
      </Modal>
    </div>
  </Page>
</template>

