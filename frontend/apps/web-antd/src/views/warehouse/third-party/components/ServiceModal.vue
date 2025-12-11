<template>
  <Modal
    :open="visible"
    :title="mode === 'create' ? '添加服务商授权' : '编辑服务商授权'"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="confirmLoading"
    width="600px"
  >
    <Form
      ref="formRef"
      :model="formState"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 16 }"
      :rules="rules"
    >
      <Form.Item label="账号别名" name="name" :rules="[{ required: true, message: '请输入账号别名' }]">
        <Input v-model:value="formState.name" placeholder="例如：主账号-4PX" />
      </Form.Item>
      
      <Form.Item label="账号代码" name="code" :rules="[{ required: true, message: '请输入账号代码' }]">
        <Input v-model:value="formState.code" placeholder="唯一标识，如 4px_main" :disabled="mode === 'edit'" />
      </Form.Item>

      <Form.Item label="服务商" name="provider_code" :rules="[{ required: true, message: '请选择服务商' }]">
        <Select v-model:value="formState.provider_code">
          <Select.Option value="4px">递四方 (4PX)</Select.Option>
          <Select.Option value="winit">万邑通 (Winit)</Select.Option>
          <Select.Option value="goodcang">谷仓</Select.Option>
          <Select.Option value="cne">CNE</Select.Option>
          <Select.Option value="yunexpress">云途</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item label="API地址" name="api_url" :rules="[{ required: true, message: '请输入API地址' }]">
        <Input v-model:value="formState.api_url" placeholder="https://api.example.com" />
      </Form.Item>

      <template v-if="formState.provider_code === '4px'">
        <Form.Item label="Customer Code" name="app_key" :rules="[{ required: true, message: '请输入Customer Code' }]">
          <Input v-model:value="formState.app_key" placeholder="4PX客户代码" />
        </Form.Item>
        <Form.Item label="Token" name="app_secret" :rules="[{ required: true, message: '请输入Token' }]">
          <Input.Password v-model:value="formState.app_secret" placeholder="4PX API Token" />
        </Form.Item>
      </template>

      <template v-else>
        <Form.Item label="App Key" name="app_key" :rules="[{ required: true, message: '请输入App Key' }]">
          <Input v-model:value="formState.app_key" placeholder="API应用密钥" />
        </Form.Item>
        <Form.Item label="App Secret" name="app_secret" :rules="[{ required: true, message: '请输入App Secret' }]">
          <Input.Password v-model:value="formState.app_secret" placeholder="API应用密钥" />
        </Form.Item>
      </template>

      <Form.Item label="状态" name="is_active">
        <Switch v-model:checked="formState.is_active" checked-children="启用" un-checked-children="禁用" />
      </Form.Item>

      <Form.Item :wrapper-col="{ offset: 6, span: 16 }">
        <Button type="primary" ghost @click="handleTestConnection" :loading="testing">
          <template #icon><CheckOutlined /></template>
          测试连接
        </Button>
        <div class="text-gray-500 text-xs mt-2">
          点击测试连接验证API配置是否正确
        </div>
      </Form.Item>
    </Form>
  </Modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { Modal, Form, Input, Select, Switch, Button, message } from 'ant-design-vue';
import { CheckOutlined } from '@ant-design/icons-vue';
import { 
  createThirdPartyService, 
  updateThirdPartyService,
  testThirdPartyConnection,
  type ServiceCreateInput,
  type ThirdPartyService 
} from '#/api/warehouse/third_party';

const props = defineProps<{ 
  visible: boolean;
  record?: ThirdPartyService | null;
  mode?: 'create' | 'edit';
}>();

const emit = defineEmits(['update:visible', 'success']);

const formRef = ref();
const confirmLoading = ref(false);
const testing = ref(false);

const formState = reactive<ServiceCreateInput & { is_active: boolean }>({
  name: '',
  code: '',
  provider_code: '4px',
  api_url: '',
  app_key: '',
  app_secret: '',
  is_active: true
});

const rules = {
  name: [{ required: true, message: '请输入账号别名' }],
  code: [{ required: true, message: '请输入账号代码' }],
  provider_code: [{ required: true, message: '请选择服务商' }],
  api_url: [{ required: true, message: '请输入API地址' }],
  app_key: [{ required: true, message: '请输入App Key/Customer Code' }],
  app_secret: [{ required: true, message: '请输入App Secret/Token' }]
};

// 监听 visible 变化
watch(() => props.visible, (val) => {
  if (val) {
    if (props.record && props.mode === 'edit') {
      // 编辑模式，填充数据
      Object.assign(formState, {
        name: props.record.name,
        code: props.record.code,
        provider_code: props.record.provider_code,
        api_url: props.record.api_url,
        app_key: props.record.app_key || '',
        app_secret: '', // 密码不显示
        is_active: props.record.is_active
      });
    } else {
      // 创建模式，重置表单
      formRef.value?.resetFields();
      Object.assign(formState, {
        name: '',
        code: '',
        provider_code: '4px',
        api_url: '',
        app_key: '',
        app_secret: '',
        is_active: true
      });
    }
  }
});

// 测试连接
const handleTestConnection = async () => {
  try {
    await formRef.value.validateFields(['api_url', 'app_key', 'app_secret']);
    
    testing.value = true;
    const result = await testThirdPartyConnection({
      provider_code: formState.provider_code,
      api_url: formState.api_url,
      app_key: formState.app_key,
      app_secret: formState.app_secret
    });
    
    if (result.success) {
      message.success('连接测试成功！');
    } else {
      message.error(`连接测试失败：${result.message || '未知错误'}`);
    }
  } catch (error: any) {
    if (error.errorFields) {
      message.error('请先填写完整的API配置信息');
    } else {
      message.error(`连接测试失败：${error.message || '未知错误'}`);
    }
  } finally {
    testing.value = false;
  }
};

const handleOk = async () => {
  try {
    await formRef.value.validate();
    confirmLoading.value = true;
    
    if (props.mode === 'edit' && props.record) {
      await updateThirdPartyService(props.record.id, formState);
      message.success('更新成功');
    } else {
      await createThirdPartyService(formState);
      message.success('创建成功');
    }
    
    emit('success');
    handleCancel();
  } catch (e: any) {
    message.error(e.message || '操作失败');
  } finally {
    confirmLoading.value = false;
  }
};

const handleCancel = () => {
  emit('update:visible', false);
};
</script>

