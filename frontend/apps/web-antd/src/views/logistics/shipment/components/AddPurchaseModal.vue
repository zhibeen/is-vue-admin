<script setup lang="ts">
/**
 * 添加采购明细Modal
 */
import { Modal, Form, FormItem, Input, InputNumber, Select, SelectOption, Row, Col, Alert, message } from 'ant-design-vue';
import { ref, watch } from 'vue';
import { createPurchaseItem } from '#/api/logistics/purchase-item';

interface Props {
  visible: boolean;
  shipmentId: number;
  shipmentStatus?: string;
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const loading = ref(false);
const formData = ref({
  purchase_order_no: '',
  sku: '',
  product_name: '',
  quantity: 0,
  unit: 'PCS',
  purchase_unit_price: 0,
  purchase_currency: 'CNY',
  supplier_name: '',
  batch_no: '',
  notes: '',
});

// 重置表单
function resetForm() {
  formData.value = {
    purchase_order_no: '',
    sku: '',
    product_name: '',
    quantity: 0,
    unit: 'PCS',
    purchase_unit_price: 0,
    purchase_currency: 'CNY',
    supplier_name: '',
    batch_no: '',
    notes: '',
  };
}

// 提交
async function handleOk() {
  // 简单验证
  if (!formData.value.sku || !formData.value.product_name) {
    message.error('请填写SKU和商品名称');
    return;
  }
  if (formData.value.quantity <= 0) {
    message.error('数量必须大于0');
    return;
  }
  if (formData.value.purchase_unit_price < 0) {
    message.error('采购单价不能为负数');
    return;
  }

  try {
    loading.value = true;
    
    // 计算总价
    const data = {
      ...formData.value,
      purchase_total_price: formData.value.quantity * formData.value.purchase_unit_price,
    };

    await createPurchaseItem(props.shipmentId, data);
    message.success('采购明细添加成功');
    
    emit('update:visible', false);
    emit('success');
    resetForm();
  } catch (error: any) {
    message.error(error.message || '添加采购明细失败');
  } finally {
    loading.value = false;
  }
}

// 取消
function handleCancel() {
  emit('update:visible', false);
  resetForm();
}

// 监听visible变化，关闭时重置表单
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    resetForm();
  }
});
</script>

<template>
  <Modal
    :open="visible"
    title="添加采购明细"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
    width="800px"
  >
    <Form layout="vertical" class="mt-4">
      <Row :gutter="16">
        <Col :span="12">
          <FormItem label="采购单号" required>
            <Input v-model:value="formData.purchase_order_no" placeholder="请输入采购单号" />
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem label="批次号">
            <Input v-model:value="formData.batch_no" placeholder="请输入批次号" />
          </FormItem>
        </Col>
      </Row>

      <Row :gutter="16">
        <Col :span="12">
          <FormItem label="SKU" required>
            <Input v-model:value="formData.sku" placeholder="请输入SKU" />
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem label="商品名称" required>
            <Input v-model:value="formData.product_name" placeholder="请输入商品名称" />
          </FormItem>
        </Col>
      </Row>

      <Row :gutter="16">
        <Col :span="8">
          <FormItem label="数量" required>
            <InputNumber
              v-model:value="formData.quantity"
              :min="1"
              :style="{ width: '100%' }"
              placeholder="请输入数量"
            />
          </FormItem>
        </Col>
        <Col :span="8">
          <FormItem label="单位">
            <Select v-model:value="formData.unit">
              <SelectOption value="PCS">PCS</SelectOption>
              <SelectOption value="件">件</SelectOption>
              <SelectOption value="套">套</SelectOption>
              <SelectOption value="个">个</SelectOption>
              <SelectOption value="千克">千克</SelectOption>
            </Select>
          </FormItem>
        </Col>
        <Col :span="8">
          <FormItem label="采购单价" required>
            <InputNumber
              v-model:value="formData.purchase_unit_price"
              :min="0"
              :precision="2"
              :style="{ width: '100%' }"
              placeholder="请输入采购单价"
            />
          </FormItem>
        </Col>
      </Row>

      <Row :gutter="16">
        <Col :span="12">
          <FormItem label="供应商名称">
            <Input v-model:value="formData.supplier_name" placeholder="请输入供应商名称" />
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem label="币种">
            <Select v-model:value="formData.purchase_currency">
              <SelectOption value="CNY">CNY 人民币</SelectOption>
              <SelectOption value="USD">USD 美元</SelectOption>
              <SelectOption value="EUR">EUR 欧元</SelectOption>
              <SelectOption value="JPY">JPY 日元</SelectOption>
            </Select>
          </FormItem>
        </Col>
      </Row>

      <FormItem label="备注">
        <Input
          v-model:value="formData.notes"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息"
        />
      </FormItem>

      <Alert
        type="info"
        show-icon
        message="采购总价将根据数量和单价自动计算"
        class="mb-4"
      />
    </Form>
  </Modal>
</template>

