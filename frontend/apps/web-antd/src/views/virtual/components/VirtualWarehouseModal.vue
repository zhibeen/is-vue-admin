<template>
  <a-modal
    v-model:visible="visible"
    :title="mode === 'create' ? '新建虚拟仓' : '编辑虚拟仓'"
    width="600px"
    :confirm-loading="confirmLoading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-form
      ref="formRef"
      :model="formState"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 16 }"
      :rules="rules"
    >
      <a-form-item label="虚拟仓编码" name="code">
        <a-input
          v-model:value="formState.code"
          placeholder="请输入虚拟仓编码"
          :disabled="mode === 'edit'"
        />
      </a-form-item>

      <a-form-item label="虚拟仓名称" name="name">
        <a-input
          v-model:value="formState.name"
          placeholder="请输入虚拟仓名称"
        />
      </a-form-item>

      <a-form-item label="仓库形态" name="category">
        <a-select
          v-model:value="formState.category"
          placeholder="请选择仓库形态"
        >
          <a-select-option value="physical">实体仓</a-select-option>
          <a-select-option value="virtual">虚拟仓</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="地理位置" name="location_type">
        <a-select
          v-model:value="formState.location_type"
          placeholder="请选择地理位置"
        >
          <a-select-option value="domestic">国内</a-select-option>
          <a-select-option value="overseas">海外</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="管理模式" name="ownership_type">
        <a-select
          v-model:value="formState.ownership_type"
          placeholder="请选择管理模式"
        >
          <a-select-option value="self">自营</a-select-option>
          <a-select-option value="third_party">第三方</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="业务类型" name="business_type">
        <a-select
          v-model:value="formState.business_type"
          placeholder="请选择业务类型"
        >
          <a-select-option value="standard">标准仓</a-select-option>
          <a-select-option value="fba">FBA仓</a-select-option>
          <a-select-option value="bonded">保税仓</a-select-option>
          <a-select-option value="transit">中转仓</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="状态" name="status">
        <a-select
          v-model:value="formState.status"
          placeholder="请选择状态"
        >
          <a-select-option value="planning">筹备中</a-select-option>
          <a-select-option value="active">正常</a-select-option>
          <a-select-option value="suspended">暂停</a-select-option>
          <a-select-option value="clearing">清退中</a-select-option>
          <a-select-option value="deprecated">已废弃</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="计价币种" name="currency">
        <a-select
          v-model:value="formState.currency"
          placeholder="请选择计价币种"
        >
          <a-select-option value="USD">USD</a-select-option>
          <a-select-option value="CNY">CNY</a-select-option>
          <a-select-option value="EUR">EUR</a-select-option>
          <a-select-option value="GBP">GBP</a-select-option>
          <a-select-option value="JPY">JPY</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="时区" name="timezone">
        <a-select
          v-model:value="formState.timezone"
          placeholder="请选择时区"
        >
          <a-select-option value="UTC">UTC</a-select-option>
          <a-select-option value="Asia/Shanghai">Asia/Shanghai (中国标准时间)</a-select-option>
          <a-select-option value="America/New_York">America/New_York (美国东部时间)</a-select-option>
          <a-select-option value="America/Los_Angeles">America/Los_Angeles (美国太平洋时间)</a-select-option>
          <a-select-option value="Europe/London">Europe/London (伦敦时间)</a-select-option>
          <a-select-option value="Europe/Berlin">Europe/Berlin (柏林时间)</a-select-option>
          <a-select-option value="Asia/Tokyo">Asia/Tokyo (东京时间)</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="容量(m³)" name="capacity">
        <a-input-number
          v-model:value="formState.capacity"
          placeholder="请输入容量"
          style="width: 100%"
          :min="0"
          :step="0.01"
        />
      </a-form-item>

      <a-form-item label="最大体积(m³)" name="max_volume">
        <a-input-number
          v-model:value="formState.max_volume"
          placeholder="请输入最大体积"
          style="width: 100%"
          :min="0"
          :step="0.01"
        />
      </a-form-item>

      <a-form-item label="备注" name="note">
        <a-textarea
          v-model:value="formState.note"
          placeholder="请输入备注"
          :rows="3"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue';
import type { FormInstance } from 'ant-design-vue';
import { message } from 'ant-design-vue';
import type { VirtualWarehouse } from '#/api/virtual';

interface Props {
  visible: boolean;
  record?: VirtualWarehouse | null;
  mode: 'create' | 'edit';
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  record: null,
  mode: 'create'
});

const emit = defineEmits<Emits>();

const formRef = ref<FormInstance>();
const confirmLoading = ref(false);

// 表单状态
const formState = reactive({
  code: '',
  name: '',
  category: 'virtual' as 'physical' | 'virtual',
  location_type: 'domestic' as 'domestic' | 'overseas',
  ownership_type: 'self' as 'self' | 'third_party',
  status: 'active' as 'planning' | 'active' | 'suspended' | 'clearing' | 'deprecated',
  business_type: 'standard',
  currency: 'USD',
  timezone: 'UTC',
  capacity: undefined as number | undefined,
  max_volume: undefined as number | undefined,
  note: ''
});

// 表单验证规则
const rules = {
  code: [
    { required: true, message: '请输入虚拟仓编码', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '编码只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入虚拟仓名称', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择仓库形态', trigger: 'change' }
  ],
  location_type: [
    { required: true, message: '请选择地理位置', trigger: 'change' }
  ],
  ownership_type: [
    { required: true, message: '请选择管理模式', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ],
  currency: [
    { required: true, message: '请选择计价币种', trigger: 'change' }
  ],
  timezone: [
    { required: true, message: '请选择时区', trigger: 'change' }
  ]
};

// 监听 visible 变化
watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => {
      if (props.record && props.mode === 'edit') {
        // 编辑模式，填充数据
        Object.assign(formState, {
          code: props.record.code,
          name: props.record.name,
          category: props.record.category,
          location_type: props.record.location_type,
          ownership_type: props.record.ownership_type,
          status: props.record.status,
          business_type: props.record.business_type,
          currency: props.record.currency,
          timezone: props.record.timezone,
          capacity: props.record.capacity,
          max_volume: props.record.max_volume,
          note: ''
        });
      } else {
        // 创建模式，重置表单
        formRef.value?.resetFields();
        Object.assign(formState, {
          code: '',
          name: '',
          category: 'virtual',
          location_type: 'domestic',
          ownership_type: 'self',
          status: 'active',
          business_type: 'standard',
          currency: 'USD',
          timezone: 'UTC',
          capacity: undefined,
          max_volume: undefined,
          note: ''
        });
      }
    });
  }
});

// 确定
const handleOk = async () => {
  try {
    await formRef.value?.validate();
    confirmLoading.value = true;

    // TODO: 调用创建/更新 API
    if (props.mode === 'create') {
      // await createVirtualWarehouse(formState);
      message.success('创建成功');
    } else {
      // await updateVirtualWarehouse(props.record!.id, formState);
      message.success('更新成功');
    }

    emit('success');
    handleCancel();
  } catch (error) {
    console.error('表单验证失败:', error);
  } finally {
    confirmLoading.value = false;
  }
};

// 取消
const handleCancel = () => {
  emit('update:visible', false);
};
</script>
