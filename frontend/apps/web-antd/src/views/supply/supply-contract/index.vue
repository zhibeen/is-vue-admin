<template>
  <div class="p-4">
    <!-- 工具栏 -->
    <Card class="mb-4">
      <Space>
        <Button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          创建开票合同
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

    <!-- 创建弹窗 -->
    <Modal
      v-model:open="modalVisible"
      title="创建开票合同"
      width="700px"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <Form
        ref="formRef"
        :model="formData"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <FormItem label="交付合同ID" name="delivery_contract_id" :rules="[{ required: true }]">
          <InputNumber v-model:value="formData.delivery_contract_id" placeholder="请输入交付合同ID" style="width: 100%" />
        </FormItem>
        
        <FormItem label="生成模式" name="mode" :rules="[{ required: true }]">
          <RadioGroup v-model:value="formData.mode">
            <Radio value="auto">自动模式（复制交付合同）</Radio>
            <Radio value="manual">手工模式（调整品名/数量）</Radio>
          </RadioGroup>
        </FormItem>
        
        <FormItem label="税率" name="tax_rate">
          <InputNumber v-model:value="formData.tax_rate" :min="0" :max="1" :step="0.01" placeholder="默认0.13" style="width: 100%" />
        </FormItem>
        
        <FormItem label="合同日期" name="contract_date" :rules="[{ required: true }]">
          <DatePicker v-model:value="formData.contract_date" style="width: 100%" />
        </FormItem>
        
        <FormItem v-if="formData.mode === 'manual'" label="开票说明" name="notes" :rules="[{ required: true }]">
          <Textarea v-model:value="formData.notes" :rows="4" placeholder="手工调整品名/数量时必须填写业务说明" />
        </FormItem>
      </Form>
      
      <Alert v-if="formData.mode === 'manual'" message="手工模式下，开票合同总金额必须与交付合同总金额一致" type="warning" class="mt-2" />
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
  InputNumber,
  RadioGroup,
  Radio,
  DatePicker,
  Textarea,
  Alert,
  message,
} from 'ant-design-vue';
import { PlusOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons-vue';
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import {
  getSupplyContractListApi,
  createSupplyContractApi,
} from '#/api/supply/supply-contract';
import type { SupplyContract, SupplyContractCreateParams } from '#/api/supply/types';

// Grid配置
const gridOptions: VxeGridProps = {
  columns: [
    { field: 'id', title: 'ID', width: 80 },
    { field: 'contract_no', title: '开票合同号', width: 150 },
    { field: 'delivery_contract_id', title: '交付合同ID', width: 120 },
    { field: 'supplier_id', title: '供应商ID', width: 100 },
    { field: 'total_amount', title: '总金额（不含税）', width: 140 },
    { field: 'total_amount_with_tax', title: '含税总额', width: 140 },
    { field: 'invoice_status', title: '开票状态', width: 120 },
    { field: 'invoiced_amount', title: '已开票金额', width: 120 },
    { field: 'contract_date', title: '合同日期', width: 120 },
    { field: 'created_at', title: '创建时间', width: 160 },
    {
      title: '操作',
      width: 100,
      fixed: 'right',
      slots: {
        default: ({ row }: { row: SupplyContract }) => [
          {
            type: 'button',
            text: '查看',
            icon: EyeOutlined,
            onClick: () => handleView(row),
          },
        ],
      },
    },
  ],
  data: [],
};

// 初始化Grid
const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions,
});

// 弹窗状态
const modalVisible = ref(false);
const formRef = ref();
const formData = reactive<Partial<SupplyContractCreateParams>>({
  delivery_contract_id: undefined,
  mode: 'auto',
  tax_rate: 0.13,
  contract_date: undefined,
  notes: '',
});

// 加载数据
async function loadData() {
  try {
    gridApi.setLoading(true);
    const res = await getSupplyContractListApi();
    gridApi.setGridOptions({ data: res || [] });
  } catch (error) {
    console.error('加载开票合同列表失败:', error);
    message.error('加载数据失败');
  } finally {
    gridApi.setLoading(false);
  }
}

// 新建
function handleCreate() {
  Object.assign(formData, {
    delivery_contract_id: undefined,
    mode: 'auto',
    tax_rate: 0.13,
    contract_date: undefined,
    notes: '',
  });
  modalVisible.value = true;
}

// 查看
function handleView(row: SupplyContract) {
  message.info(`查看开票合同: ${row.contract_no}`);
  // TODO: 跳转到详情页
}

// 弹窗确定
async function handleModalOk() {
  try {
    await formRef.value.validate();
    await createSupplyContractApi(formData as SupplyContractCreateParams);
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

