<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Modal, Form, Input, InputNumber, Checkbox, message, Select } from 'ant-design-vue';
import { createCustomsProduct, updateCustomsProduct, type CustomsProduct } from '#/api/customs/product';
import { getDictItemsApi, type DictItem } from '#/api/system/dict';

const props = defineProps<{
  open: boolean;
  record: CustomsProduct | null;
}>();

const emit = defineEmits(['update:open', 'success']);

const loading = ref(false);
const formRef = ref();
const unitOptions = ref<DictItem[]>([]);

const formState = ref<Partial<CustomsProduct>>({
  name: '',
  hs_code: '',
  rebate_rate: 0,
  unit: undefined,
  elements: '',
  description: '',
  is_active: true
});

const rules = {
  name: [{ required: true, message: '请输入报关名称', trigger: 'blur' }],
  hs_code: [{ required: true, message: '请输入HS编码', trigger: 'blur' }],
  unit: [{ required: true, message: '请选择申报单位', trigger: 'change' }]
};

const isEdit = computed(() => !!props.record?.id);
const title = computed(() => isEdit.value ? '编辑报关品类' : '新建报关品类');

watch(
  () => props.open,
  (val) => {
    if (val) {
      loadUnits();
      if (props.record) {
        formState.value = { ...props.record };
      } else {
        formState.value = { 
            name: '',
            hs_code: '',
            rebate_rate: 0.13,
            unit: undefined,
            is_active: true 
        };
      }
    }
  }
);

async function loadUnits() {
    if (unitOptions.value.length > 0) return;
    try {
        unitOptions.value = await getDictItemsApi('customs_unit');
    } catch (e) { console.error(e); }
}

async function handleOk() {
  try {
    await formRef.value?.validate();
    loading.value = true;
    
    // 清洗数据，移除 VxeTable 注入的字段和 id
    const payload = { ...formState.value };
    delete (payload as any).id;
    delete (payload as any)._X_ROW_KEY;
    
    if (isEdit.value && props.record?.id) {
        await updateCustomsProduct(props.record.id, payload);
        message.success('更新成功');
    } else {
        await createCustomsProduct(payload);
        message.success('创建成功');
    }
    
    emit('success');
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}


function handleCancel() {
  emit('update:open', false);
}
</script>

<template>
  <Modal
    :open="open"
    :title="title"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
    width="600px"
  >
    <Form
      ref="formRef"
      :model="formState"
      :rules="rules"
      layout="vertical"
    >
      <Form.Item label="报关通用名称" name="name" help="海关规范申报名称，如：汽车前大灯总成">
        <Input v-model:value="formState.name" placeholder="请输入名称" />
      </Form.Item>
      
      <Form.Item label="HS编码 (10位)" name="hs_code">
        <Input v-model:value="formState.hs_code" placeholder="如：8512201000" />
      </Form.Item>

      <div class="grid grid-cols-2 gap-4">
          <Form.Item label="退税率" name="rebate_rate">
            <InputNumber 
                v-model:value="formState.rebate_rate" 
                :min="0" :max="1" :step="0.01" 
                style="width: 100%"
                :formatter="value => `${(value * 100).toFixed(0)}%`"
                :parser="value => parseFloat(value.replace('%', '')) / 100"
            />
          </Form.Item>
          
          <Form.Item label="申报单位" name="unit">
            <Select 
                v-model:value="formState.unit" 
                placeholder="请选择单位" 
                show-search
                option-filter-prop="label"
                :options="unitOptions"
            />
          </Form.Item>
      </div>

      <Form.Item label="申报要素模板" name="elements" help="格式：品牌|型号|适用车型... (竖线分隔)">
        <Input.TextArea v-model:value="formState.elements" :rows="3" placeholder="品牌|型号|..." />
      </Form.Item>
      
      <Form.Item label="备注" name="description">
        <Input.TextArea v-model:value="formState.description" :rows="2" />
      </Form.Item>

      <Form.Item name="is_active">
        <Checkbox v-model:checked="formState.is_active">启用</Checkbox>
      </Form.Item>
    </Form>
  </Modal>
</template>

