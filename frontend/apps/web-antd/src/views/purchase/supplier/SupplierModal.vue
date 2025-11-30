<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue';
import { useVbenModal } from '@vben/common-ui';
import { 
  Form, Input, InputNumber, Select, Row, Col, Tabs, TabPane, 
  Card, Button, Space, Divider, message 
} from 'ant-design-vue';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { createSupplier, updateSupplier } from '#/api/purchase/supplier';
import { getPaymentTerms } from '#/api/serc/finance';
import type { SysSupplier } from '#/api/purchase/model';

const emit = defineEmits(['success']);

const data = ref<SysSupplier | null>(null);
const isUpdate = ref(false);
const activeTab = ref('1');
const loading = ref(false);
const paymentTermOptions = ref<any[]>([]);

onMounted(async () => {
  try {
    const res = await getPaymentTerms();
    paymentTermOptions.value = res || [];
  } catch (e) {
    console.error('Failed to load payment terms', e);
  }
});

// Form State
const formState = reactive<Partial<SysSupplier>>({
  code: '',
  name: '',
  short_name: '',
  supplier_type: 'manufacturer',
  status: 'active',
  grade: 'C',
  country: '',
  province: '',
  city: '',
  address: '',
  website: '',
  primary_contact: '',
  primary_phone: '',
  primary_email: '',
  contacts: [],
  tax_id: '',
  currency: 'CNY',
  payment_term_id: undefined,
  payment_terms: '',
  payment_method: '',
  bank_accounts: [],
  lead_time_days: undefined,
  moq: '',
  notes: '',
  tags: []
});

// Rules
const rules = {
  name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入供应商代码', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
  supplier_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
};

const [Modal, modalApi] = useVbenModal({
  title: computed(() => isUpdate.value ? '编辑供应商' : '新增供应商'),
  draggable: true,
  onConfirm: handleSubmit,
  onOpenChange: (isOpen) => {
    if (isOpen) {
      const { data: record, isUpdate: update } = modalApi.getData();
      isUpdate.value = update;
      data.value = record;
      
      // Reset form
      Object.assign(formState, {
        code: '',
        name: '',
        short_name: '',
        supplier_type: 'manufacturer',
        status: 'active',
        grade: 'C',
        country: '',
        province: '',
        city: '',
        address: '',
        website: '',
        primary_contact: '',
        primary_phone: '',
        primary_email: '',
        contacts: [],
        tax_id: '',
        currency: 'CNY',
        payment_term_id: undefined,
        payment_terms: '',
        payment_method: '',
        bank_accounts: [],
        lead_time_days: undefined,
        moq: '',
        notes: '',
        tags: []
      });

      if (update && record) {
        Object.assign(formState, JSON.parse(JSON.stringify(record)));
        // Ensure arrays are initialized
        if (!formState.contacts) formState.contacts = [];
        if (!formState.bank_accounts) formState.bank_accounts = [];
        if (!formState.tags) formState.tags = [];
      }
      
      activeTab.value = '1';
    }
  },
});

async function handleSubmit() {
  try {
    loading.value = true;
    modalApi.setState({ confirmLoading: true });
    
    // Validate manually if needed, but Form usually handles it via rules
    // Here we just submit
    
    if (isUpdate.value && data.value?.id) {
      await updateSupplier(data.value.id, formState);
      message.success('更新成功');
    } else {
      await createSupplier(formState);
      message.success('创建成功');
    }
    
    emit('success');
    modalApi.close();
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
    modalApi.setState({ confirmLoading: false });
  }
}

// Dynamic Bank Accounts
const addBankAccount = () => {
  if (!formState.bank_accounts) formState.bank_accounts = [];
  formState.bank_accounts.push({
    bank_name: '',
    account: '',
    currency: 'CNY',
    swift: '',
    purpose: ''
  });
};

const removeBankAccount = (index: number) => {
  formState.bank_accounts?.splice(index, 1);
};

// Dynamic Contacts
const addContact = () => {
  if (!formState.contacts) formState.contacts = [];
  formState.contacts.push({
    name: '',
    role: '',
    phone: '',
    email: ''
  });
};

const removeContact = (index: number) => {
  formState.contacts?.splice(index, 1);
};

// Options
const supplierTypeOptions = [
  { label: '生产商', value: 'manufacturer' },
  { label: '贸易商', value: 'trader' },
  { label: '服务商', value: 'service_provider' },
  { label: '其他', value: 'other' }
];

const statusOptions = [
  { label: '活跃', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '黑名单', value: 'blacklisted' },
  { label: '潜在', value: 'potential' }
];

const gradeOptions = [
  { label: 'A级', value: 'A' },
  { label: 'B级', value: 'B' },
  { label: 'C级', value: 'C' },
  { label: 'D级', value: 'D' }
];

const currencyOptions = [
  { label: '人民币 (CNY)', value: 'CNY' },
  { label: '美元 (USD)', value: 'USD' },
  { label: '欧元 (EUR)', value: 'EUR' },
  { label: '港币 (HKD)', value: 'HKD' }
];
</script>

<template>
  <Modal class="w-[800px]">
    <Form layout="vertical" :model="formState" :rules="rules">
      <Tabs v-model:activeKey="activeTab">
        
        <!-- 基础信息 -->
        <TabPane key="1" tab="基础信息">
          <Row :gutter="16">
            <Col :span="12">
              <Form.Item label="供应商代码" name="code">
                <Input v-model:value="formState.code" placeholder="如：SUP-001" :disabled="isUpdate" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="供应商名称" name="name">
                <Input v-model:value="formState.name" placeholder="完整注册名称" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="简称" name="short_name">
                <Input v-model:value="formState.short_name" placeholder="内部使用简称" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="类型" name="supplier_type">
                <Select v-model:value="formState.supplier_type" :options="supplierTypeOptions" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="状态" name="status">
                <Select v-model:value="formState.status" :options="statusOptions" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="等级" name="grade">
                <Select v-model:value="formState.grade" :options="gradeOptions" />
              </Form.Item>
            </Col>
            <Col :span="24">
              <Form.Item label="标签" name="tags">
                <Select v-model:value="formState.tags" mode="tags" placeholder="输入标签后按回车" />
              </Form.Item>
            </Col>
          </Row>
        </TabPane>

        <!-- 联系信息 -->
        <TabPane key="2" tab="联系信息">
          <Divider orientation="left">主要地址</Divider>
          <Row :gutter="16">
            <Col :span="8">
              <Form.Item label="国家/地区" name="country">
                <Input v-model:value="formState.country" />
              </Form.Item>
            </Col>
            <Col :span="8">
              <Form.Item label="省份" name="province">
                <Input v-model:value="formState.province" />
              </Form.Item>
            </Col>
            <Col :span="8">
              <Form.Item label="城市" name="city">
                <Input v-model:value="formState.city" />
              </Form.Item>
            </Col>
            <Col :span="24">
              <Form.Item label="详细地址" name="address">
                <Input v-model:value="formState.address" />
              </Form.Item>
            </Col>
            <Col :span="24">
              <Form.Item label="官网" name="website">
                <Input v-model:value="formState.website" placeholder="https://" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">首要联系人</Divider>
          <Row :gutter="16">
            <Col :span="8">
              <Form.Item label="姓名" name="primary_contact">
                <Input v-model:value="formState.primary_contact" />
              </Form.Item>
            </Col>
            <Col :span="8">
              <Form.Item label="电话" name="primary_phone">
                <Input v-model:value="formState.primary_phone" />
              </Form.Item>
            </Col>
            <Col :span="8">
              <Form.Item label="Email" name="primary_email">
                <Input v-model:value="formState.primary_email" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">
            其他联系人
            <Button type="link" size="small" @click="addContact">
              <PlusOutlined /> 添加
            </Button>
          </Divider>
          <div class="space-y-2">
            <div v-for="(contact, index) in formState.contacts" :key="index" class="flex items-start space-x-2 border border-border p-2 rounded">
              <Input v-model:value="contact.name" placeholder="姓名" class="w-1/4" />
              <Input v-model:value="contact.role" placeholder="职位" class="w-1/4" />
              <Input v-model:value="contact.phone" placeholder="电话" class="w-1/4" />
              <Input v-model:value="contact.email" placeholder="Email" class="w-1/4" />
              <Button type="text" danger @click="removeContact(index)">
                <MinusCircleOutlined />
              </Button>
            </div>
            <div v-if="!formState.contacts?.length" class="text-text-secondary text-center py-2">
              暂无其他联系人
            </div>
          </div>
        </TabPane>

        <!-- 财务信息 -->
        <TabPane key="3" tab="财务信息">
          <Row :gutter="16">
            <Col :span="12">
              <Form.Item label="税号/VAT号" name="tax_id">
                <Input v-model:value="formState.tax_id" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="默认结算币种" name="currency">
                <Select v-model:value="formState.currency" :options="currencyOptions" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="付款条款" name="payment_term_id">
                <Select 
                  v-model:value="formState.payment_term_id" 
                  :options="paymentTermOptions" 
                  :field-names="{ label: 'name', value: 'id' }"
                  placeholder="请选择标准条款"
                  allow-clear
                />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="付款方式" name="payment_method">
                <Select 
                  v-model:value="formState.payment_method" 
                  placeholder="请选择付款方式"
                  allow-clear
                >
                  <Select.Option value="T/T">银行转账 (T/T)</Select.Option>
                  <Select.Option value="L/C">信用证 (L/C)</Select.Option>
                  <Select.Option value="Draft">承兑汇票</Select.Option>
                  <Select.Option value="Cash">现金</Select.Option>
                  <Select.Option value="Check">支票</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="条款备注 (旧/自定义)" name="payment_terms">
                <Input v-model:value="formState.payment_terms" placeholder="如有特殊约定请备注" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">
            银行账户
            <Button type="link" size="small" @click="addBankAccount">
              <PlusOutlined /> 添加账户
            </Button>
          </Divider>
          
          <div class="space-y-3">
            <Card 
              v-for="(account, index) in formState.bank_accounts" 
              :key="index"
              size="small"
              class="border border-border shadow-sm"
              :bodyStyle="{ padding: '12px' }"
            >
              <template #extra>
                <Button type="text" danger size="small" @click="removeBankAccount(index)">
                  <MinusCircleOutlined /> 删除
                </Button>
              </template>
              <Row :gutter="12">
                <Col :span="12">
                  <Form.Item label="开户行" class="mb-2">
                    <Input v-model:value="account.bank_name" placeholder="银行名称" />
                  </Form.Item>
                </Col>
                <Col :span="12">
                  <Form.Item label="账号" class="mb-2">
                    <Input v-model:value="account.account" placeholder="银行账号" />
                  </Form.Item>
                </Col>
                <Col :span="8">
                  <Form.Item label="币种" class="mb-2">
                    <Select v-model:value="account.currency" :options="currencyOptions" />
                  </Form.Item>
                </Col>
                <Col :span="8">
                  <Form.Item label="SWIFT/IBAN" class="mb-2">
                    <Input v-model:value="account.swift" placeholder="SWIFT Code" />
                  </Form.Item>
                </Col>
                <Col :span="8">
                  <Form.Item label="用途" class="mb-2">
                    <Input v-model:value="account.purpose" placeholder="例如: 基本户" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
            <div v-if="!formState.bank_accounts?.length" class="text-text-secondary text-center py-4 border border-dashed border-border rounded">
              暂无银行账户信息
            </div>
          </div>
        </TabPane>

        <!-- 运营信息 -->
        <TabPane key="4" tab="运营信息">
          <Row :gutter="16">
            <Col :span="12">
              <Form.Item label="平均交货期 (天)" name="lead_time_days">
                <InputNumber v-model:value="formState.lead_time_days" class="w-full" :min="0" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item label="最小起订量 (MOQ)" name="moq">
                <Input v-model:value="formState.moq" placeholder="例如: 1000 PCS" />
              </Form.Item>
            </Col>
            <Col :span="24">
              <Form.Item label="备注" name="notes">
                <Input.TextArea v-model:value="formState.notes" :rows="4" />
              </Form.Item>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </Form>
  </Modal>
</template>

