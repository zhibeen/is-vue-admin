<script setup lang="ts">
/**
 * 物流服务创建/编辑表单
 */
import { ref, watch, computed, onMounted } from 'vue';
import { message, Modal, Form, Input, Select, InputNumber, Textarea } from 'ant-design-vue';
import { 
  getShipmentLogisticsServiceById,
  addShipmentLogisticsService,
  updateShipmentLogisticsService,
  type ShipmentLogisticsServiceCreate
} from '#/api/logistics/shipment-logistics-service';
import { getLogisticsProviders } from '#/api/logistics/logistics-provider';

const props = defineProps<{
  visible: boolean;
  shipmentId: number;
  serviceId: number | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const formRef = ref();
const loading = ref(false);
const formData = ref<ShipmentLogisticsServiceCreate>({
  logistics_provider_id: 0,
  service_type: '',
  service_description: '',
  estimated_amount: undefined,
  actual_amount: undefined,
  currency: 'CNY',
  payment_method: '',
  notes: '',
});

// 物流服务商选项
const providerOptions = ref<any[]>([]);

const isEdit = computed(() => props.serviceId !== null);
const title = computed(() => isEdit.value ? '编辑物流服务' : '添加物流服务');

// 服务类型选项
const serviceTypeOptions = [
  { label: '国内卡车运输', value: 'domestic_trucking' },
  { label: '国际海运', value: 'international_sea' },
  { label: '国际空运', value: 'international_air' },
  { label: '清关服务', value: 'customs_clearance' },
  { label: '目的国派送', value: 'destination_delivery' },
];

// 付款方式选项
const paymentMethodOptions = [
  { label: '预付', value: 'prepaid' },
  { label: '即付', value: 'immediate' },
  { label: '后付', value: 'postpaid' },
];

// 表单验证规则
const rules = {
  logistics_provider_id: [{ required: true, message: '请选择物流服务商' }],
  service_type: [{ required: true, message: '请选择服务类型' }],
};

// 加载物流服务商列表
async function loadProviders() {
  try {
    const data = await getLogisticsProviders({ is_active: true });
    providerOptions.value = data.map((p: any) => ({
      label: p.provider_name,
      value: p.id,
    }));
  } catch (e: any) {
    message.error('加载服务商失败');
  }
}

// 加载数据
async function loadData() {
  if (!props.serviceId) return;
  
  try {
    loading.value = true;
    const data = await getShipmentLogisticsServiceById(props.shipmentId, props.serviceId);
    formData.value = {
      logistics_provider_id: data.logistics_provider_id,
      service_type: data.service_type,
      service_description: data.service_description,
      estimated_amount: data.estimated_amount,
      actual_amount: data.actual_amount,
      currency: data.currency,
      payment_method: data.payment_method,
      notes: data.notes,
    };
  } catch (e: any) {
    message.error('加载失败: ' + (e.message || '未知错误'));
  } finally {
    loading.value = false;
  }
}

// 监听弹窗显示
watch(() => props.visible, (val) => {
  if (val) {
    loadProviders();
    loadData();
  }
});

onMounted(() => {
  loadProviders();
});

// 提交
async function handleSubmit() {
  try {
    await formRef.value.validate();
    
    loading.value = true;
    
    if (isEdit.value) {
      await updateShipmentLogisticsService(
        props.shipmentId, 
        props.serviceId!, 
        formData.value
      );
      message.success('更新成功');
    } else {
      await addShipmentLogisticsService(props.shipmentId, formData.value);
      message.success('添加成功');
    }
    
    emit('close');
  } catch (e: any) {
    if (e.errorFields) {
      // 表单验证失败
      return;
    }
    message.error('操作失败: ' + (e.message || '未知错误'));
  } finally {
    loading.value = false;
  }
}

// 取消
function handleCancel() {
  emit('close');
}
</script>

<template>
  <Modal
    :open="visible"
    :title="title"
    :confirm-loading="loading"
    width="700px"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <Form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 16 }"
    >
      <Form.Item label="物流服务商" name="logistics_provider_id">
        <Select 
          v-model:value="formData.logistics_provider_id" 
          placeholder="请选择物流服务商"
          :options="providerOptions"
          show-search
          :filter-option="(input: string, option: any) => {
            return option.label.toLowerCase().includes(input.toLowerCase());
          }"
        />
      </Form.Item>
      
      <Form.Item label="服务类型" name="service_type">
        <Select 
          v-model:value="formData.service_type" 
          placeholder="请选择服务类型"
          :options="serviceTypeOptions"
        />
      </Form.Item>
      
      <Form.Item label="服务描述" name="service_description">
        <Textarea 
          v-model:value="formData.service_description" 
          placeholder="请输入服务描述"
          :rows="2"
        />
      </Form.Item>
      
      <Form.Item label="预估费用" name="estimated_amount">
        <InputNumber 
          v-model:value="formData.estimated_amount" 
          placeholder="请输入预估费用"
          :min="0"
          :precision="2"
          style="width: 100%;"
          :controls="false"
        >
          <template #addonAfter>
            <span>元</span>
          </template>
        </InputNumber>
      </Form.Item>
      
      <Form.Item label="实际费用" name="actual_amount">
        <InputNumber 
          v-model:value="formData.actual_amount" 
          placeholder="请输入实际费用"
          :min="0"
          :precision="2"
          style="width: 100%;"
          :controls="false"
        >
          <template #addonAfter>
            <span>元</span>
          </template>
        </InputNumber>
      </Form.Item>
      
      <Form.Item label="币种" name="currency">
        <Select 
          v-model:value="formData.currency" 
          placeholder="请选择币种"
          :options="[
            { label: '人民币(CNY)', value: 'CNY' },
            { label: '美元(USD)', value: 'USD' },
            { label: '欧元(EUR)', value: 'EUR' },
          ]"
        />
      </Form.Item>
      
      <Form.Item label="付款方式" name="payment_method">
        <Select 
          v-model:value="formData.payment_method" 
          placeholder="请选择付款方式"
          :options="paymentMethodOptions"
        />
      </Form.Item>
      
      <Form.Item label="备注" name="notes">
        <Textarea 
          v-model:value="formData.notes" 
          placeholder="请输入备注信息"
          :rows="3"
        />
      </Form.Item>
    </Form>
  </Modal>
</template>

