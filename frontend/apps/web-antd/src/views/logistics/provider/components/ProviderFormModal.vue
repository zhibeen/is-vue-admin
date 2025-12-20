<script setup lang="ts">
/**
 * 物流服务商创建/编辑表单
 */
import { ref, watch, computed } from 'vue';
import { message, Modal, Form, Input, Select, Switch, Textarea } from 'ant-design-vue';
import { 
  getLogisticsProviderById,
  createLogisticsProvider,
  updateLogisticsProvider,
  type LogisticsProviderCreate
} from '#/api/logistics/logistics-provider';

const props = defineProps<{
  visible: boolean;
  providerId: number | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const formRef = ref();
const loading = ref(false);
const formData = ref<LogisticsProviderCreate>({
  provider_name: '',
  provider_code: '',
  service_type: undefined,
  payment_method: undefined,
  settlement_cycle: undefined,
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  bank_name: '',
  bank_account: '',
  bank_account_name: '',
  service_areas: [],
  is_active: true,
  notes: '',
});

const isEdit = computed(() => props.providerId !== null);
const title = computed(() => isEdit.value ? '编辑物流服务商' : '新建物流服务商');

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

// 结算周期选项
const settlementCycleOptions = [
  { label: '即时结算', value: 'immediate' },
  { label: '周结', value: 'weekly' },
  { label: '月结', value: 'monthly' },
];

// 表单验证规则
const rules = {
  provider_name: [{ required: true, message: '请输入服务商名称' }],
  provider_code: [
    { required: true, message: '请输入服务商编码' },
    { min: 2, message: '编码至少需要2个字符' }
  ],
};

// 加载数据
async function loadData() {
  if (!props.providerId) return;
  
  try {
    loading.value = true;
    const data = await getLogisticsProviderById(props.providerId);
    formData.value = {
      provider_name: data.provider_name,
      provider_code: data.provider_code,
      service_type: data.service_type,
      payment_method: data.payment_method,
      settlement_cycle: data.settlement_cycle,
      contact_name: data.contact_name,
      contact_phone: data.contact_phone,
      contact_email: data.contact_email,
      bank_name: data.bank_name,
      bank_account: data.bank_account,
      bank_account_name: data.bank_account_name,
      service_areas: data.service_areas || [],
      is_active: data.is_active,
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
    loadData();
  }
});

// 提交
async function handleSubmit() {
  try {
    await formRef.value.validate();
    
    loading.value = true;
    
    if (isEdit.value) {
      await updateLogisticsProvider(props.providerId!, formData.value);
      message.success('更新成功');
    } else {
      await createLogisticsProvider(formData.value);
      message.success('创建成功');
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
    width="800px"
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
      <!-- 基本信息 -->
      <div class="mb-4 text-base font-semibold">基本信息</div>
      
      <Form.Item label="服务商名称" name="provider_name">
        <Input v-model:value="formData.provider_name" placeholder="请输入服务商名称" />
      </Form.Item>
      
      <Form.Item label="服务商编码" name="provider_code">
        <Input 
          v-model:value="formData.provider_code" 
          placeholder="请输入服务商编码"
          :disabled="isEdit"
        />
      </Form.Item>
      
      <Form.Item label="服务类型" name="service_type">
        <Select 
          v-model:value="formData.service_type" 
          placeholder="请选择服务类型"
          :options="serviceTypeOptions"
        />
      </Form.Item>
      
      <Form.Item label="付款方式" name="payment_method">
        <Select 
          v-model:value="formData.payment_method" 
          placeholder="请选择付款方式"
          :options="paymentMethodOptions"
        />
      </Form.Item>
      
      <Form.Item label="结算周期" name="settlement_cycle">
        <Select 
          v-model:value="formData.settlement_cycle" 
          placeholder="请选择结算周期"
          :options="settlementCycleOptions"
        />
      </Form.Item>
      
      <Form.Item label="启用状态" name="is_active">
        <Switch v-model:checked="formData.is_active" />
      </Form.Item>
      
      <!-- 联系信息 -->
      <div class="mb-4 mt-6 text-base font-semibold">联系信息</div>
      
      <Form.Item label="联系人" name="contact_name">
        <Input v-model:value="formData.contact_name" placeholder="请输入联系人姓名" />
      </Form.Item>
      
      <Form.Item label="联系电话" name="contact_phone">
        <Input v-model:value="formData.contact_phone" placeholder="请输入联系电话" />
      </Form.Item>
      
      <Form.Item label="邮箱" name="contact_email">
        <Input v-model:value="formData.contact_email" placeholder="请输入邮箱地址" />
      </Form.Item>
      
      <!-- 银行信息 -->
      <div class="mb-4 mt-6 text-base font-semibold">银行信息</div>
      
      <Form.Item label="开户银行" name="bank_name">
        <Input v-model:value="formData.bank_name" placeholder="请输入开户银行" />
      </Form.Item>
      
      <Form.Item label="银行账号" name="bank_account">
        <Input v-model:value="formData.bank_account" placeholder="请输入银行账号" />
      </Form.Item>
      
      <Form.Item label="账户名称" name="bank_account_name">
        <Input v-model:value="formData.bank_account_name" placeholder="请输入账户名称" />
      </Form.Item>
      
      <!-- 其他信息 -->
      <div class="mb-4 mt-6 text-base font-semibold">其他信息</div>
      
      <Form.Item label="服务区域" name="service_areas">
        <Select 
          v-model:value="formData.service_areas" 
          mode="tags"
          placeholder="请输入服务区域（可输入多个）"
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

