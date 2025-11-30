<script setup lang="ts">
import { useVbenModal } from '@vben/common-ui';
import { createCompany, updateCompany } from '#/api/serc/foundation';
import { message, Tabs, TabPane, Form, Input, Select, InputNumber, DatePicker, Textarea, Button, Space, Card } from 'ant-design-vue';
import { ref, reactive } from 'vue';
import type { SysCompany } from '#/api/serc/model';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons-vue';

const emit = defineEmits(['success']);
const isUpdate = ref(false);
const recordId = ref<number | null>(null);
const activeTab = ref('basic');

// 表单数据
const formState = reactive<Partial<SysCompany>>({
  legal_name: '',
  short_name: '',
  english_name: '',
  company_type: '一般纳税人',
  status: 'active',
  unified_social_credit_code: '',
  tax_id: '',
  business_license_no: '',
  registered_address: '',
  business_address: '',
  postal_code: '',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  fax: '',
  tax_rate: 0.13,
  bank_accounts: [], // 初始化为空数组
  customs_code: '',
  customs_registration_no: '',
  inspection_code: '',
  foreign_trade_operator_code: '',
  forex_account: '',
  forex_registration_no: '',
  import_export_license_no: '',
  default_currency: 'CNY',
  default_payment_term: '',
  credit_limit: undefined,
  settlement_cycle: 30,
  notes: '',
});

// 表单验证规则
const rules = {
  legal_name: [{ required: true, message: '请输入法定名称', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
};

const formRef = ref();

// 银行账户操作
const addBankAccount = () => {
  if (!formState.bank_accounts) {
    formState.bank_accounts = [];
  }
  formState.bank_accounts.push({
    bank_name: '',
    account_number: '',
    account_name: formState.legal_name || '', // 默认使用公司名称
    currency: 'CNY',
    is_default: false,
    purpose: '收付款',
    swift_code: '',
  });
};

const removeBankAccount = (index: number) => {
  formState.bank_accounts?.splice(index, 1);
};

const [Modal, modalApi] = useVbenModal({
  title: '采购主体',
  class: 'w-[900px]',
  onConfirm: async () => {
    try {
      await formRef.value?.validate();
      
      if (isUpdate.value && recordId.value) {
        await updateCompany(recordId.value, formState);
        message.success('更新成功');
      } else {
        await createCompany(formState);
        message.success('创建成功');
      }
      
      emit('success');
      modalApi.close();
    } catch (e: any) {
      console.error('表单验证失败:', e);
      if (e.errorFields) {
        message.error('请检查表单填写');
      } else {
        message.error('操作失败');
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = modalApi.getData();
      isUpdate.value = !!data?.id;
      recordId.value = data?.id || null;
      activeTab.value = 'basic';
      
      if (isUpdate.value && data) {
        // 更新模式：填充数据
        Object.assign(formState, data);
      } else {
        // 创建模式：重置表单
        Object.assign(formState, {
          legal_name: '',
          short_name: '',
          english_name: '',
          company_type: '一般纳税人',
          status: 'active',
          unified_social_credit_code: '',
          tax_id: '',
          business_license_no: '',
          registered_address: '',
          business_address: '',
          postal_code: '',
          contact_person: '',
          contact_phone: '',
          contact_email: '',
          fax: '',
          tax_rate: 0.13,
          bank_accounts: [],
          customs_code: '',
          customs_registration_no: '',
          inspection_code: '',
          foreign_trade_operator_code: '',
          forex_account: '',
          forex_registration_no: '',
          import_export_license_no: '',
          default_currency: 'CNY',
          default_payment_term: '',
          credit_limit: undefined,
          settlement_cycle: 30,
          notes: '',
        });
      }
    }
  },
});
</script>

<template>
  <Modal>
    <Form
      ref="formRef"
      :model="formState"
      :rules="rules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
    >
      <Tabs v-model:activeKey="activeTab">
        <!-- 基础信息 -->
        <TabPane key="basic" tab="基础信息">
          <Form.Item label="法定名称" name="legal_name">
            <Input v-model:value="formState.legal_name" placeholder="请输入公司法定名称" />
          </Form.Item>
          <Form.Item label="简称" name="short_name">
            <Input v-model:value="formState.short_name" placeholder="请输入公司简称" />
          </Form.Item>
          <Form.Item label="英文名称" name="english_name">
            <Input v-model:value="formState.english_name" placeholder="请输入英文名称" />
          </Form.Item>
          <Form.Item label="公司类型" name="company_type">
            <Select v-model:value="formState.company_type" placeholder="请选择公司类型">
              <Select.Option value="一般纳税人">一般纳税人</Select.Option>
              <Select.Option value="小规模纳税人">小规模纳税人</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="状态" name="status">
            <Select v-model:value="formState.status" placeholder="请选择状态">
              <Select.Option value="active">正常</Select.Option>
              <Select.Option value="inactive">停用</Select.Option>
              <Select.Option value="suspended">暂停</Select.Option>
            </Select>
          </Form.Item>
        </TabPane>

        <!-- 证照信息 -->
        <TabPane key="license" tab="证照信息">
          <Form.Item label="统一社会信用代码" name="unified_social_credit_code">
            <Input v-model:value="formState.unified_social_credit_code" placeholder="18位统一社会信用代码 (五证合一)" maxlength="18" />
          </Form.Item>
          <Form.Item label="增值税率" name="tax_rate">
            <InputNumber 
              v-model:value="formState.tax_rate" 
              :min="0" 
              :max="1" 
              :step="0.01" 
              placeholder="如：0.13"
              style="width: 100%"
            />
          </Form.Item>
        </TabPane>

        <!-- 联系信息 -->
        <TabPane key="contact" tab="联系信息">
          <Form.Item label="注册地址" name="registered_address">
            <Textarea v-model:value="formState.registered_address" placeholder="营业执照上的注册地址" :rows="2" />
          </Form.Item>
          <Form.Item label="经营地址" name="business_address">
            <Textarea v-model:value="formState.business_address" placeholder="实际办公地址" :rows="2" />
          </Form.Item>
          <Form.Item label="邮政编码" name="postal_code">
            <Input v-model:value="formState.postal_code" placeholder="邮政编码" />
          </Form.Item>
          <Form.Item label="联系人" name="contact_person">
            <Input v-model:value="formState.contact_person" placeholder="联系人姓名" />
          </Form.Item>
          <Form.Item label="联系电话" name="contact_phone">
            <Input v-model:value="formState.contact_phone" placeholder="联系电话" />
          </Form.Item>
          <Form.Item label="联系邮箱" name="contact_email">
            <Input v-model:value="formState.contact_email" type="email" placeholder="联系邮箱" />
          </Form.Item>
          <Form.Item label="传真" name="fax">
            <Input v-model:value="formState.fax" placeholder="传真号码" />
          </Form.Item>
        </TabPane>

        <!-- 银行账户 -->
        <TabPane key="bank" tab="银行账户">
          <div class="mb-4">
            <Button type="dashed" block @click="addBankAccount">
              <PlusOutlined /> 添加银行账户
            </Button>
          </div>
          
          <div v-if="formState.bank_accounts && formState.bank_accounts.length > 0" class="space-y-4">
            <Card 
              v-for="(account, index) in formState.bank_accounts" 
              :key="index"
              size="small"
              class="border border-border"
              :body-style="{ padding: '16px' }"
            >
              <template #extra>
                <MinusCircleOutlined 
                  class="cursor-pointer text-error hover:text-red-700" 
                  @click="removeBankAccount(index)" 
                />
              </template>
              
              <div class="grid grid-cols-2 gap-4">
                <Form.Item 
                  label="开户银行" 
                  :name="['bank_accounts', index, 'bank_name']"
                  :rules="{ required: true, message: '请输入开户银行' }"
                >
                  <Input v-model:value="account.bank_name" placeholder="如：中国银行深圳分行" />
                </Form.Item>
                
                <Form.Item 
                  label="银行账号" 
                  :name="['bank_accounts', index, 'account_number']"
                  :rules="{ required: true, message: '请输入银行账号' }"
                >
                  <Input v-model:value="account.account_number" placeholder="银行账号" />
                </Form.Item>
                
                <Form.Item label="账户名称" :name="['bank_accounts', index, 'account_name']">
                  <Input v-model:value="account.account_name" placeholder="默认与公司名一致" />
                </Form.Item>
                
                <Form.Item label="币种" :name="['bank_accounts', index, 'currency']">
                  <Select v-model:value="account.currency" style="width: 100%">
                    <Select.Option value="CNY">人民币 (CNY)</Select.Option>
                    <Select.Option value="USD">美元 (USD)</Select.Option>
                    <Select.Option value="EUR">欧元 (EUR)</Select.Option>
                    <Select.Option value="HKD">港币 (HKD)</Select.Option>
                  </Select>
                </Form.Item>
                
                <Form.Item label="SWIFT Code" :name="['bank_accounts', index, 'swift_code']">
                  <Input v-model:value="account.swift_code" placeholder="境外汇款必填" />
                </Form.Item>
                
                <Form.Item label="用途" :name="['bank_accounts', index, 'purpose']">
                  <Input v-model:value="account.purpose" placeholder="如：基本户/外汇户" />
                </Form.Item>
              </div>
            </Card>
          </div>
          <div v-else class="text-center text-text-secondary py-8">
            暂无银行账户，请点击上方按钮添加
          </div>
        </TabPane>

        <!-- 跨境资质 -->
        <TabPane key="crossborder" tab="跨境资质">
          <Form.Item label="海关编码" name="customs_code">
            <Input v-model:value="formState.customs_code" placeholder="10位海关编码 (CR Code)" maxlength="10" />
          </Form.Item>
          <Form.Item label="对外贸易经营者备案号" name="foreign_trade_operator_code">
            <Input v-model:value="formState.foreign_trade_operator_code" placeholder="对外贸易经营者备案号" />
          </Form.Item>
        </TabPane>

        <!-- 业务配置 -->
        <TabPane key="business" tab="业务配置">
          <Form.Item label="默认币种" name="default_currency">
            <Select v-model:value="formState.default_currency" placeholder="请选择默认币种">
              <Select.Option value="CNY">人民币 (CNY)</Select.Option>
              <Select.Option value="USD">美元 (USD)</Select.Option>
              <Select.Option value="EUR">欧元 (EUR)</Select.Option>
              <Select.Option value="GBP">英镑 (GBP)</Select.Option>
              <Select.Option value="JPY">日元 (JPY)</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="默认付款条款" name="default_payment_term">
            <Input v-model:value="formState.default_payment_term" placeholder="如：T/T 30天" />
          </Form.Item>
          <Form.Item label="信用额度" name="credit_limit">
            <InputNumber 
              v-model:value="formState.credit_limit" 
              :min="0" 
              :precision="2"
              placeholder="信用额度"
              style="width: 100%"
            />
          </Form.Item>
          <Form.Item label="结算周期（天）" name="settlement_cycle">
            <InputNumber 
              v-model:value="formState.settlement_cycle" 
              :min="0" 
              placeholder="结算周期"
              style="width: 100%"
            />
          </Form.Item>
        </TabPane>

        <!-- 备注 -->
        <TabPane key="notes" tab="备注">
          <Form.Item label="备注信息" name="notes">
            <Textarea 
              v-model:value="formState.notes" 
              placeholder="其他备注信息" 
              :rows="6"
            />
          </Form.Item>
        </TabPane>
      </Tabs>
    </Form>
  </Modal>
</template>

<style scoped>
:deep(.ant-tabs-content) {
  max-height: 500px;
  overflow-y: auto;
}
</style>

