<template>
  <div class="p-4">
    <!-- 工具栏 -->
    <Card class="mb-4">
      <Space>
        <Button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          新建发货单
        </Button>
        <Button @click="handleRefresh">
          <template #icon><ReloadOutlined /></template>
          刷新
        </Button>
      </Space>
    </Card>

    <!-- 列表 -->
    <Card>
      <Grid ref="gridRef" />
    </Card>

    <!-- 创建/编辑弹窗 -->
    <Modal
      v-model:open="modalVisible"
      :title="modalTitle"
      width="900px"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <Form
        ref="formRef"
        :model="formData"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <FormItem label="发货公司" name="shipper_company_id" :rules="[{ required: true }]">
          <Select v-model:value="formData.shipper_company_id" placeholder="请选择发货公司">
            <!-- TODO: 从API加载公司列表 -->
            <SelectOption :value="1">默认公司</SelectOption>
          </Select>
        </FormItem>
        
        <FormItem label="收货人" name="consignee_name">
          <Input v-model:value="formData.consignee_name" placeholder="请输入收货人名称" />
        </FormItem>
        
        <FormItem label="收货国家" name="consignee_country">
          <Input v-model:value="formData.consignee_country" placeholder="请输入收货国家" />
        </FormItem>
        
        <FormItem label="物流商" name="logistics_provider">
          <Input v-model:value="formData.logistics_provider" placeholder="请输入物流商" />
        </FormItem>
        
        <FormItem label="运输方式" name="shipping_method">
          <Select v-model:value="formData.shipping_method" placeholder="请选择运输方式">
            <SelectOption value="sea">海运</SelectOption>
            <SelectOption value="air">空运</SelectOption>
            <SelectOption value="express">快递</SelectOption>
          </Select>
        </FormItem>
        
        <FormItem label="预计发货日期" name="estimated_ship_date">
          <DatePicker v-model:value="formData.estimated_ship_date" style="width: 100%" />
        </FormItem>
        
        <FormItem label="备注" name="notes">
          <Textarea v-model:value="formData.notes" :rows="3" placeholder="请输入备注" />
        </FormItem>
      </Form>
      
      <Divider>发货明细</Divider>
      
      <!-- 简化版明细输入 - 实际项目中应该使用更复杂的表格编辑组件 -->
      <Alert message="实际项目中需要使用表格组件编辑明细，此处简化处理" type="info" class="mb-2" />
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import {
  Card,
  Button,
  Space,
  Modal,
  Form,
  FormItem,
  Input,
  Select,
  SelectOption,
  DatePicker,
  Textarea,
  Divider,
  Alert,
  message,
} from 'ant-design-vue';
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined } from '@ant-design/icons-vue';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import {
  getShipmentListApi,
  createShipmentApi,
  updateShipmentApi,
  deleteShipmentApi,
  generateContractsApi,
} from '#/api/logistics';
import type { ShipmentOrder, ShipmentOrderCreateParams } from '#/api/logistics/types';

// Grid配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 80 },
    { field: 'shipment_no', title: '发货单号', width: 150 },
    { field: 'status', title: '状态', width: 100 },
    { field: 'consignee_name', title: '收货人', width: 150 },
    { field: 'logistics_provider', title: '物流商', width: 120 },
    { field: 'shipping_method', title: '运输方式', width: 100 },
    { field: 'total_amount', title: '总金额', width: 120 },
    { field: 'is_contracted', title: '是否已生成合同', width: 140,
      slots: { default: ({ row }: { row: ShipmentOrder }) => row.is_contracted ? '是' : '否' }
    },
    { field: 'created_at', title: '创建时间', width: 160 },
    {
      title: '操作',
      width: 280,
      fixed: 'right',
      slots: {
        default: ({ row }: { row: ShipmentOrder }) => [
          {
            type: 'button',
            text: '生成合同',
            icon: CheckCircleOutlined,
            disabled: row.is_contracted,
            onClick: () => handleGenerateContracts(row),
          },
          {
            type: 'button',
            text: '编辑',
            icon: EditOutlined,
            onClick: () => handleEdit(row),
          },
          {
            type: 'button',
            text: '删除',
            icon: DeleteOutlined,
            danger: true,
            onClick: () => handleDelete(row),
          },
        ],
      },
    },
  ],
  data: [],
  pagerConfig: {
    enabled: true,
  },
};

// 初始化Grid
const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions,
});

// 弹窗状态
const modalVisible = ref(false);
const modalTitle = ref('新建发货单');
const formRef = ref();
const formData = reactive<Partial<ShipmentOrderCreateParams>>({
  shipper_company_id: undefined,
  consignee_name: '',
  consignee_country: '',
  logistics_provider: '',
  shipping_method: '',
  estimated_ship_date: undefined,
  notes: '',
  items: [],
});

// 加载数据
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getShipmentListApi({ page: 1, per_page: 20 });
    gridApi.setGridOptions({ data: res.items || [] });
  } catch (error) {
    console.error('加载发货单列表失败:', error);
    message.error('加载数据失败');
  } finally {
    gridApi.setLoading(false);
  }
}

// 新建
function handleCreate() {
  modalTitle.value = '新建发货单';
  Object.assign(formData, {
    shipper_company_id: undefined,
    consignee_name: '',
    consignee_country: '',
    logistics_provider: '',
    shipping_method: '',
    estimated_ship_date: undefined,
    notes: '',
    items: [],
  });
  modalVisible.value = true;
}

// 编辑
function handleEdit(row: ShipmentOrder) {
  modalTitle.value = '编辑发货单';
  Object.assign(formData, row);
  modalVisible.value = true;
}

// 删除
async function handleDelete(row: ShipmentOrder) {
  try {
    await deleteShipmentApi(row.id);
    message.success('删除成功');
    loadData();
  } catch (error) {
    console.error('删除失败:', error);
    message.error('删除失败');
  }
}

// 生成交付合同
async function handleGenerateContracts(row: ShipmentOrder) {
  try {
    const res = await generateContractsApi(row.id);
    message.success(`成功生成 ${res.contract_count} 个交付合同`);
    loadData();
  } catch (error) {
    console.error('生成交付合同失败:', error);
    message.error('生成交付合同失败');
  }
}

// 弹窗确定
async function handleModalOk() {
  try {
    await formRef.value.validate();
    // TODO: 实际项目中需要收集明细数据
    const params: ShipmentOrderCreateParams = {
      ...formData as any,
      items: [
        {
          sku: 'DEMO-001',
          product_name: '示例商品',
          quantity: 100,
          unit_price: 50,
          total_price: 5000,
          supplier_id: 1,
        },
      ],
    };
    
    await createShipmentApi(params);
    message.success('创建成功');
    modalVisible.value = false;
    loadData();
  } catch (error) {
    console.error('创建失败:', error);
    message.error('创建失败');
  }
}

// 弹窗取消
function handleModalCancel() {
  modalVisible.value = false;
}

// 刷新
function handleRefresh() {
  loadData();
}

// 挂载时加载数据
onMounted(() => {
  loadData();
});
</script>

<style scoped>
/* 样式可以根据需要添加 */
</style>

