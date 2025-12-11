<template>
  <a-modal
    v-model:visible="visible"
    :title="mode === 'create' ? '新建分配策略' : '编辑分配策略'"
    width="700px"
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
      <a-form-item label="策略模式" name="policy_mode">
        <a-select
          v-model:value="formState.policy_mode"
          placeholder="请选择策略模式"
        >
          <a-select-option value="override">覆盖模式</a-select-option>
          <a-select-option value="inherit">继承模式</a-select-option>
        </a-select>
        <div class="text-gray-500 text-xs mt-1">
          覆盖模式：强制覆盖低级规则；继承模式：与低级规则叠加
        </div>
      </a-form-item>

      <a-form-item label="优先级" name="priority">
        <a-input-number
          v-model:value="formState.priority"
          placeholder="请输入优先级"
          style="width: 100%"
          :min="0"
          :max="999"
        />
        <div class="text-gray-500 text-xs mt-1">
          数字越大优先级越高，用于相同级别的策略排序
        </div>
      </a-form-item>

      <a-form-item label="源仓库" name="source_warehouse_id">
        <a-select
          v-model:value="formState.source_warehouse_id"
          placeholder="请选择源仓库（留空表示全局）"
          allow-clear
        >
          <!-- TODO: 从仓库列表加载 -->
          <a-select-option :value="1">国内总仓</a-select-option>
          <a-select-option :value="2">美东仓</a-select-option>
          <a-select-option :value="3">美西仓</a-select-option>
        </a-select>
      </a-form-item>

      <a-divider>分配范围（四选一）</a-divider>

      <a-form-item label="SKU级别" name="sku">
        <a-input
          v-model:value="formState.sku"
          placeholder="请输入SKU（单品级策略）"
          allow-clear
        />
        <div class="text-gray-500 text-xs mt-1">
          针对单个SKU的特例策略，优先级最高
        </div>
      </a-form-item>

      <a-form-item label="SKU分组" name="warehouse_product_group_id">
        <a-select
          v-model:value="formState.warehouse_product_group_id"
          placeholder="请选择SKU分组（分组级策略）"
          allow-clear
        >
          <!-- TODO: 从SKU分组列表加载 -->
          <a-select-option :value="1">黑五大促组</a-select-option>
          <a-select-option :value="2">清仓处理组</a-select-option>
          <a-select-option :value="3">新品推广组</a-select-option>
        </a-select>
        <div class="text-gray-500 text-xs mt-1">
          针对人工圈选的SKU团，优先级次之
        </div>
      </a-form-item>

      <a-form-item label="产品品类" name="category_id">
        <a-select
          v-model:value="formState.category_id"
          placeholder="请选择产品品类（品类级策略）"
          allow-clear
        >
          <!-- TODO: 从产品品类列表加载 -->
          <a-select-option :value="1">汽车配件</a-select-option>
          <a-select-option :value="2">电子产品</a-select-option>
          <a-select-option :value="3">家居用品</a-select-option>
        </a-select>
        <div class="text-gray-500 text-xs mt-1">
          针对产品线的批量策略
        </div>
      </a-form-item>

      <div class="text-gray-500 text-xs mb-4 ml-24">
        <p>注意：如果以上三个字段都为空，则表示仓库级策略（默认保底策略）</p>
        <p>策略优先级：SKU > 分组 > 品类 > 仓库</p>
      </div>

      <a-divider>分配规则</a-divider>

      <a-form-item label="分配方式">
        <a-radio-group v-model:value="allocationType">
          <a-radio value="ratio">按比例分配</a-radio>
          <a-radio value="fixed">固定数量</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item v-if="allocationType === 'ratio'" label="分配比例" name="ratio">
        <a-input-number
          v-model:value="formState.ratio"
          placeholder="请输入分配比例"
          style="width: 100%"
          :min="0"
          :max="1"
          :step="0.01"
          :formatter="value => `${(value * 100).toFixed(1)}%`"
          :parser="value => parseFloat(value!.replace('%', '')) / 100"
        />
        <div class="text-gray-500 text-xs mt-1">
          例如：0.8 表示分配80%的库存
        </div>
      </a-form-item>

      <a-form-item v-if="allocationType === 'fixed'" label="固定数量" name="fixed_amount">
        <a-input-number
          v-model:value="formState.fixed_amount"
          placeholder="请输入固定数量"
          style="width: 100%"
          :min="0"
          :step="1"
        />
        <div class="text-gray-500 text-xs mt-1">
          锁定指定数量的库存
        </div>
      </a-form-item>

      <a-form-item label="生效时间" name="effective_from">
        <a-range-picker
          v-model:value="effectiveRange"
          style="width: 100%"
          :show-time="{ format: 'HH:mm' }"
          format="YYYY-MM-DD HH:mm"
          :placeholder="['开始时间', '结束时间']"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick, computed } from 'vue';
import type { FormInstance } from 'ant-design-vue';
import { message } from 'ant-design-vue';
import type { AllocationPolicy, PolicyForm } from '#/api/virtual';
import dayjs from 'dayjs';

interface Props {
  visible: boolean;
  virtualWarehouseId: number;
  record?: AllocationPolicy | null;
  mode: 'create' | 'edit';
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  virtualWarehouseId: 0,
  record: null,
  mode: 'create'
});

const emit = defineEmits<Emits>();

const formRef = ref<FormInstance>();
const confirmLoading = ref(false);
const allocationType = ref<'ratio' | 'fixed'>('ratio');
const effectiveRange = ref<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

// 表单状态
const formState = reactive<PolicyForm>({
  source_warehouse_id: undefined,
  category_id: undefined,
  warehouse_product_group_id: undefined,
  sku: undefined,
  ratio: undefined,
  fixed_amount: undefined,
  priority: 0,
  policy_mode: 'override'
});

// 表单验证规则
const rules = {
  priority: [
    { required: true, message: '请输入优先级', trigger: 'blur' },
    { type: 'number', min: 0, max: 999, message: '优先级必须在0-999之间', trigger: 'blur' }
  ],
  policy_mode: [
    { required: true, message: '请选择策略模式', trigger: 'change' }
  ],
  ratio: [
    { 
      validator: (_rule, value) => {
        if (allocationType.value === 'ratio' && (value === undefined || value === null)) {
          return Promise.reject('请输入分配比例');
        }
        if (value !== undefined && value !== null && (value < 0 || value > 1)) {
          return Promise.reject('分配比例必须在0-1之间');
        }
        return Promise.resolve();
      },
      trigger: 'blur'
    }
  ],
  fixed_amount: [
    { 
      validator: (_rule, value) => {
        if (allocationType.value === 'fixed' && (value === undefined || value === null)) {
          return Promise.reject('请输入固定数量');
        }
        if (value !== undefined && value !== null && value < 0) {
          return Promise.reject('固定数量必须大于等于0');
        }
        return Promise.resolve();
      },
      trigger: 'blur'
    }
  ]
};

// 监听分配类型变化
watch(allocationType, (newVal) => {
  if (newVal === 'ratio') {
    formState.fixed_amount = undefined;
  } else {
    formState.ratio = undefined;
  }
});

// 监听 visible 变化
watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => {
      if (props.record && props.mode === 'edit') {
        // 编辑模式，填充数据
        Object.assign(formState, {
          source_warehouse_id: props.record.source_warehouse_id,
          category_id: props.record.category_id,
          warehouse_product_group_id: props.record.warehouse_product_group_id,
          sku: props.record.sku,
          ratio: props.record.ratio,
          fixed_amount: props.record.fixed_amount,
          priority: props.record.priority,
          policy_mode: props.record.policy_mode
        });

        // 设置分配类型
        if (props.record.ratio !== undefined && props.record.ratio !== null) {
          allocationType.value = 'ratio';
        } else if (props.record.fixed_amount !== undefined && props.record.fixed_amount !== null) {
          allocationType.value = 'fixed';
        }

        // 设置生效时间
        if (props.record.effective_from && props.record.effective_to) {
          effectiveRange.value = [dayjs(props.record.effective_from), dayjs(props.record.effective_to)];
        } else {
          effectiveRange.value = null;
        }
      } else {
        // 创建模式，重置表单
        formRef.value?.resetFields();
        Object.assign(formState, {
          source_warehouse_id: undefined,
          category_id: undefined,
          warehouse_product_group_id: undefined,
          sku: undefined,
          ratio: undefined,
          fixed_amount: undefined,
          priority: 0,
          policy_mode: 'override'
        });
        allocationType.value = 'ratio';
        effectiveRange.value = null;
      }
    });
  }
});

// 确定
const handleOk = async () => {
  try {
    await formRef.value?.validate();
    confirmLoading.value = true;

    // 准备提交数据
    const submitData: PolicyForm = {
      ...formState,
      // 根据分配类型清理不需要的字段
      ratio: allocationType.value === 'ratio' ? formState.ratio : undefined,
      fixed_amount: allocationType.value === 'fixed' ? formState.fixed_amount : undefined
    };

    // 设置生效时间
    if (effectiveRange.value) {
      submitData.effective_from = effectiveRange.value[0].format('YYYY-MM-DD HH:mm:ss');
      submitData.effective_to = effectiveRange.value[1].format('YYYY-MM-DD HH:mm:ss');
    }

    // TODO: 调用创建/更新 API
    if (props.mode === 'create') {
      // await createPolicy(props.virtualWarehouseId, submitData);
      message.success('创建成功');
    } else {
      // await updatePolicy(props.record!.id, submitData);
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
