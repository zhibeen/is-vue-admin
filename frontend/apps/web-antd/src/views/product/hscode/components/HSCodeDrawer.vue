<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { 
  Drawer, 
  Form, 
  Input, 
  InputNumber, 
  Button, 
  Space, 
  Divider, 
  Row, 
  Col,
  Select,
  message 
} from 'ant-design-vue';
import type { Rule } from 'ant-design-vue/es/form';
import type { SysHSCode } from '#/api/serc/model';
import { createHSCode, updateHSCode } from '#/api/serc/foundation';

const emit = defineEmits(['success', 'register']);

const visible = ref(false);
const isUpdate = ref(false);
const loading = ref(false);
const title = computed(() => isUpdate.value ? '编辑 HS 编码' : '新增 HS 编码');

const formRef = ref();
const formState = reactive<Partial<SysHSCode>>({
  code: '',
  name: '',
  unit_1: '',
  unit_2: '',
  default_transaction_unit: '',
  refund_rate: 0,
  import_mfn_rate: 0,
  import_general_rate: 0,
  vat_rate: 0,
  regulatory_code: '',
  inspection_code: '',
  elements: '',
  note: ''
});

const rules: Record<string, Rule[]> = {
  code: [{ required: true, message: '请输入 HS 编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  refund_rate: [{ required: true, message: '请输入出口退税率', trigger: 'change', type: 'number' }],
};

async function open(record?: SysHSCode) {
  visible.value = true;
  isUpdate.value = !!record;
  
  if (record) {
    Object.assign(formState, record);
  } else {
    resetForm();
  }
}

function resetForm() {
  Object.assign(formState, {
    id: undefined,
    code: '',
    name: '',
    unit_1: '',
    unit_2: '',
    default_transaction_unit: '',
    refund_rate: 0,
    import_mfn_rate: 0,
    import_general_rate: 0,
    vat_rate: 0.13, // Default VAT
    regulatory_code: '',
    inspection_code: '',
    elements: '',
    note: ''
  });
  formRef.value?.clearValidate();
}

function close() {
  visible.value = false;
  loading.value = false;
}

async function handleSubmit() {
  try {
    await formRef.value?.validate();
    loading.value = true;
    
    if (isUpdate.value && formState.id) {
      await updateHSCode(formState.id, formState);
      message.success('更新成功');
    } else {
      await createHSCode(formState);
      message.success('创建成功');
    }
    
    emit('success');
    close();
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

defineExpose({ open });
</script>

<template>
  <Drawer
    v-model:open="visible"
    :title="title"
    width="700"
    :footer-style="{ textAlign: 'right' }"
  >
    <Form
      ref="formRef"
      :model="formState"
      :rules="rules"
      layout="vertical"
    >
      <!-- 基础信息 -->
      <Divider orientation="left">基础信息</Divider>
      <Row :gutter="16">
        <Col :span="12">
          <Form.Item label="HS 编码" name="code">
            <Input v-model:value="formState.code" placeholder="请输入 10 位 HS 编码" />
          </Form.Item>
        </Col>
        <Col :span="12">
          <Form.Item label="商品名称" name="name">
            <Input v-model:value="formState.name" placeholder="请输入商品名称" />
          </Form.Item>
        </Col>
      </Row>

      <!-- 税率信息 -->
      <Divider orientation="left">税率配置</Divider>
      <Row :gutter="16">
        <Col :span="6">
          <Form.Item label="出口退税率" name="refund_rate" help="例如 0.13 表示 13%">
             <InputNumber v-model:value="formState.refund_rate" :min="0" :max="1" :step="0.01" style="width: 100%" />
          </Form.Item>
        </Col>
        <Col :span="6">
          <Form.Item label="增值税率" name="vat_rate">
             <InputNumber v-model:value="formState.vat_rate" :min="0" :max="1" :step="0.01" style="width: 100%" />
          </Form.Item>
        </Col>
        <Col :span="6">
          <Form.Item label="进口最惠国" name="import_mfn_rate">
             <InputNumber v-model:value="formState.import_mfn_rate" :min="0" :max="1" :step="0.01" style="width: 100%" />
          </Form.Item>
        </Col>
        <Col :span="6">
          <Form.Item label="进口普通" name="import_general_rate">
             <InputNumber v-model:value="formState.import_general_rate" :min="0" :max="1" :step="0.01" style="width: 100%" />
          </Form.Item>
        </Col>
      </Row>

      <!-- 计量单位 -->
      <Divider orientation="left">计量单位</Divider>
      <Row :gutter="16">
        <Col :span="8">
          <Form.Item label="第一法定单位" name="unit_1">
            <Input v-model:value="formState.unit_1" placeholder="如：千克" />
          </Form.Item>
        </Col>
        <Col :span="8">
          <Form.Item label="第二法定单位" name="unit_2">
            <Input v-model:value="formState.unit_2" placeholder="如：个" />
          </Form.Item>
        </Col>
        <Col :span="8">
          <Form.Item label="建议申报单位" name="default_transaction_unit">
            <Input v-model:value="formState.default_transaction_unit" placeholder="如：个" />
          </Form.Item>
        </Col>
      </Row>

      <!-- 监管信息 -->
      <Divider orientation="left">监管信息</Divider>
      <Row :gutter="16">
        <Col :span="12">
          <Form.Item label="监管证件代码" name="regulatory_code">
            <Input v-model:value="formState.regulatory_code" placeholder="如：A/B" />
          </Form.Item>
        </Col>
        <Col :span="12">
          <Form.Item label="检验检疫类别" name="inspection_code">
             <Input v-model:value="formState.inspection_code" placeholder="如：M/N" />
          </Form.Item>
        </Col>
      </Row>
      
      <!-- 申报要素与备注 -->
      <Divider orientation="left">其他信息</Divider>
      <Form.Item label="申报要素" name="elements" help="格式：1:品名;2:品牌;...">
        <Input.TextArea v-model:value="formState.elements" :rows="4" placeholder="请输入申报要素" />
      </Form.Item>
      
      <Form.Item label="备注" name="note">
        <Input.TextArea v-model:value="formState.note" :rows="2" />
      </Form.Item>

    </Form>

    <template #footer>
      <Space>
        <Button @click="close">取消</Button>
        <Button type="primary" :loading="loading" @click="handleSubmit">确认</Button>
      </Space>
    </template>
  </Drawer>
</template>

