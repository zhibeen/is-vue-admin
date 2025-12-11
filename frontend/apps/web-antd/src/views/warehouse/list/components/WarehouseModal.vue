<template>
  <Modal
    :open="visible"
    :title="mode === 'create' ? '新建仓库' : '编辑仓库'"
    width="800px"
    :confirm-loading="confirmLoading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <Tabs v-model:activeKey="activeTabKey" class="warehouse-modal-tabs">
      <!-- Tab 1: 仓库属性 -->
      <Tabs.TabPane key="properties" tab="仓库属性">
        <div class="tab-content">
    <Form
      ref="formRef"
      :model="formState"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 16 }"
      :rules="rules"
    >
      <Form.Item label="仓库编码" name="code">
        <Input
          v-model:value="formState.code"
          placeholder="请输入仓库编码"
          :disabled="mode === 'edit'"
        />
        <div class="text-gray-500 text-xs mt-1">
          编码唯一，用于系统识别
        </div>
      </Form.Item>

      <Form.Item label="仓库名称" name="name">
        <Input
          v-model:value="formState.name"
          placeholder="请输入仓库名称"
        />
      </Form.Item>

      <Row :gutter="16">
        <Col :span="12">
          <Form.Item label="仓库形态" name="category">
            <Select
              v-model:value="formState.category"
              placeholder="请选择仓库形态"
            >
              <Select.Option value="physical">实体仓</Select.Option>
              <Select.Option value="virtual">虚拟仓</Select.Option>
            </Select>
          </Form.Item>
        </Col>
        <Col :span="12">
          <Form.Item label="地理位置" name="location_type">
            <Select
              v-model:value="formState.location_type"
              placeholder="请选择地理位置"
            >
              <Select.Option value="domestic">国内</Select.Option>
              <Select.Option value="overseas">海外</Select.Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row :gutter="16">
        <Col :span="12">
          <Form.Item label="管理模式" name="ownership_type">
            <Select
              v-model:value="formState.ownership_type"
              placeholder="请选择管理模式"
            >
              <Select.Option value="self">自营</Select.Option>
              <Select.Option value="third_party">第三方</Select.Option>
            </Select>
          </Form.Item>
        </Col>
        <Col :span="12">
          <Form.Item label="状态" name="status">
            <Select
              v-model:value="formState.status"
              placeholder="请选择状态"
            >
              <Select.Option value="planning">筹备中</Select.Option>
              <Select.Option value="active">正常</Select.Option>
              <Select.Option value="suspended">暂停</Select.Option>
              <Select.Option value="clearing">清退中</Select.Option>
              <Select.Option value="deprecated">已废弃</Select.Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row :gutter="16">
        <Col :span="12">
          <Form.Item label="业务类型" name="business_type">
            <Select
              v-model:value="formState.business_type"
              placeholder="请选择业务类型"
              allow-clear
            >
              <Select.Option value="standard">标准仓</Select.Option>
              <Select.Option value="fba">FBA仓</Select.Option>
              <Select.Option value="bonded">保税仓</Select.Option>
              <Select.Option value="transit">中转仓</Select.Option>
            </Select>
          </Form.Item>
        </Col>
        <Col :span="12">
          <Form.Item label="计价币种" name="currency">
            <Select
              v-model:value="formState.currency"
              placeholder="请选择计价币种"
            >
              <Select.Option value="USD">USD</Select.Option>
              <Select.Option value="CNY">CNY</Select.Option>
              <Select.Option value="EUR">EUR</Select.Option>
              <Select.Option value="GBP">GBP</Select.Option>
              <Select.Option value="JPY">JPY</Select.Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Form.Item label="时区" name="timezone">
        <Select
          v-model:value="formState.timezone"
          placeholder="请选择时区"
        >
          <Select.Option value="UTC">UTC</Select.Option>
          <Select.Option value="Asia/Shanghai">Asia/Shanghai (中国标准时间)</Select.Option>
          <Select.Option value="America/New_York">America/New_York (美国东部时间)</Select.Option>
          <Select.Option value="America/Los_Angeles">America/Los_Angeles (美国太平洋时间)</Select.Option>
          <Select.Option value="Europe/London">Europe/London (伦敦时间)</Select.Option>
        </Select>
      </Form.Item>

            <!-- 虚拟仓配置：仅虚拟仓显示 -->
            <div v-if="formState.category === 'virtual'" class="conditional-section">
              <div class="section-title">虚拟仓配置</div>
              <Form.Item label="关联子仓">
        <Select
          v-model:value="formState.child_warehouse_ids"
          :options="physicalWarehouseOptions" 
          mode="multiple"
          allow-clear
          style="width: 100%"
          placeholder="请选择关联的实体子仓"
        />
        <div class="text-gray-500 text-xs mt-1">
          虚拟仓可以关联多个实体仓作为子仓
        </div>
      </Form.Item>
            </div>

            <!-- 第三方配置：仅第三方管理模式显示 -->
            <div v-if="formState.ownership_type === 'third_party'" class="conditional-section">
              <div class="section-title">第三方服务商配置</div>
        <Form.Item label="服务商" name="third_party_service_id" :rules="[{ required: true, message: '请选择服务商' }]">
          <Select
            v-model:value="formState.third_party_service_id"
            placeholder="请选择第三方服务商"
            :options="thirdPartyServiceOptions.map(s => ({ label: s.name, value: s.id }))"
          />
        </Form.Item>
        
        <Form.Item label="外部仓库" name="third_party_warehouse_id" :rules="[{ required: true, message: '请绑定外部仓库' }]">
          <div class="flex gap-2">
            <Select
              v-model:value="formState.third_party_warehouse_id"
              placeholder="请选择外部仓库"
              class="flex-1"
            >
              <Select.Option 
                v-for="wh in remoteWarehouseOptions" 
                :key="wh.id" 
                :value="wh.id"
                :disabled="wh.is_bound && wh.id !== formState.third_party_warehouse_id"
              >
                {{ wh.name }} ({{ wh.code }}) 
                <span v-if="wh.is_bound && wh.id !== formState.third_party_warehouse_id" class="text-xs text-red-400">
                  [已绑定: {{ wh.bound_warehouse_name }}]
                </span>
              </Select.Option>
            </Select>
            <Button 
              type="primary" 
              ghost 
              :loading="syncLoading" 
              @click="handleSyncWarehouses"
              :disabled="!formState.third_party_service_id"
            >
              <template #icon><ReloadOutlined /></template>
              刷新
            </Button>
          </div>
          <div class="text-gray-500 text-xs mt-1">
                  如列表中没有您需要的仓库，请点击"刷新"按钮从服务商全量同步。
          </div>
        </Form.Item>
      </div>
          </Form>
        </div>
      </Tabs.TabPane>

      <!-- Tab 2: 物理属性（仅自营实体仓显示） -->
      <Tabs.TabPane 
        key="physical" 
        tab="物理属性" 
        :disabled="!shouldShowPhysicalTab"
      >
        <div class="tab-content">
          <Form
            ref="formRef"
            :model="formState"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 16 }"
          >
            <div v-if="shouldShowPhysicalTab">
              <div class="mb-4 text-gray-500">
                以下属性仅适用于自营实体仓库
              </div>
              <Row :gutter="16">
                <Col :span="12">
                  <Form.Item label="容量" name="capacity">
                    <InputNumber
                      v-model:value="formState.capacity"
                      placeholder="请输入容量"
                      style="width: 100%"
                      :min="0"
                      :step="0.01"
                    />
                    <div class="text-gray-500 text-xs mt-1">
                      仓库存储能力（如：货位数、重量吨等）
                    </div>
                  </Form.Item>
                </Col>
                <Col :span="12">
                  <Form.Item label="最大体积(m³)" name="max_volume">
                    <InputNumber
                      v-model:value="formState.max_volume"
                      placeholder="请输入最大体积"
                      style="width: 100%"
                      :min="0"
                      :step="0.01"
                    />
                    <div class="text-gray-500 text-xs mt-1">
                      最大存储体积，汽配行业按体积计费
                    </div>
                  </Form.Item>
                </Col>
              </Row>
            </div>
            <div v-else class="text-center py-8 text-gray-400">
              <div class="text-lg mb-2">当前仓库配置不支持物理属性</div>
              <div>物理属性仅适用于自营实体仓库</div>
              <div class="text-sm mt-2">
                • 虚拟仓库没有物理实体<br>
                • 第三方仓库的物理属性由服务商管理
              </div>
            </div>
          </Form>
        </div>
      </Tabs.TabPane>

      <!-- Tab 3: 联系人信息 -->
      <Tabs.TabPane key="contact" tab="联系人信息">
        <div class="tab-content">
          <Form
            ref="formRef"
            :model="formState"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 16 }"
          >
            <Form.Item label="负责人" name="contact_person">
              <Input
                v-model:value="formState.contact_person"
                placeholder="请输入负责人姓名"
              />
            </Form.Item>

            <Form.Item label="联系电话" name="contact_phone">
              <Input
                v-model:value="formState.contact_phone"
                placeholder="请输入联系电话"
              />
            </Form.Item>

            <Form.Item label="地址" name="address">
              <Textarea
                v-model:value="formState.address"
                placeholder="请输入仓库地址"
                :rows="3"
              />
            </Form.Item>
    </Form>
        </div>
      </Tabs.TabPane>
    </Tabs>
  </Modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick, computed } from 'vue';
import type { FormInstance } from 'ant-design-vue';
import { 
  Modal, 
  Form, 
  Input, 
  Select, 
  Row, 
  Col, 
  InputNumber,
  Textarea,
  message,
  Button,
  Tabs
} from 'ant-design-vue';
import { 
  getThirdPartyServices, 
  getThirdPartyWarehouses, 
  syncThirdPartyWarehouses,
  type ThirdPartyService,
  type ThirdPartyWarehouse
} from '#/api/warehouse/third_party';
import { ReloadOutlined } from '@ant-design/icons-vue';
import { 
  createWarehouse,
  getWarehouseList,
  updateWarehouse,
  type Warehouse,
  type WarehouseForm
} from '#/api/warehouse';

interface Props {
  visible: boolean;
  record?: Warehouse | null;
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
const activeTabKey = ref('properties'); // 默认激活仓库属性Tab

// 表单状态
const formState = reactive<WarehouseForm>({
  code: '',
  name: '',
  category: 'physical',
  location_type: 'domestic',
  ownership_type: 'self',
  status: 'active',
  business_type: 'standard',
  currency: 'USD',
  timezone: 'UTC',
  capacity: undefined,
  max_volume: undefined,
  contact_person: '',
  contact_phone: '',
  address: '',
  child_warehouse_ids: [],
  api_config: undefined,
  third_party_service_id: undefined,
  third_party_warehouse_id: undefined
});

// 三方服务商选项
const thirdPartyServiceOptions = ref<ThirdPartyService[]>([]);
// 远程仓库选项
const remoteWarehouseOptions = ref<ThirdPartyWarehouse[]>([]);
const syncLoading = ref(false);

// API配置文本（用于JSON编辑）
const apiConfigText = ref('');

// 物理仓库选项（用于虚拟仓关联）
const physicalWarehouseOptions = ref<{ label: string; value: number }[]>([]);

// 加载三方服务商
const loadThirdPartyServices = async () => {
  const res = await getThirdPartyServices();
  thirdPartyServiceOptions.value = res;
};

// 加载远程仓库
const loadRemoteWarehouses = async (serviceId: number) => {
  if (!serviceId) {
    remoteWarehouseOptions.value = [];
    return;
  }
  const res = await getThirdPartyWarehouses(serviceId);
  remoteWarehouseOptions.value = res;
};

// 手动全量同步
const handleSyncWarehouses = async () => {
  const serviceId = formState.third_party_service_id;
  if (!serviceId) {
    message.warning('请先选择服务商');
    return;
  }
  
  try {
    syncLoading.value = true;
    const { synced_count } = await syncThirdPartyWarehouses(serviceId);
    message.success(`同步成功，更新了 ${synced_count} 个仓库`);
    // 重新加载列表
    await loadRemoteWarehouses(serviceId);
  } catch (error) {
    console.error(error);
  } finally {
    syncLoading.value = false;
  }
};

// 监听服务商变更
watch(() => formState.third_party_service_id, (newVal) => {
  formState.third_party_warehouse_id = undefined; // 重置已选仓库
  if (newVal) {
    loadRemoteWarehouses(newVal);
  } else {
    remoteWarehouseOptions.value = [];
  }
});

// 计算属性：是否显示物理属性Tab（仅自营实体仓）
const shouldShowPhysicalTab = computed(() => {
  return formState.category === 'physical' && formState.ownership_type === 'self';
});

// 监听仓库形态或管理模式变更，如果切换到非自营实体仓，自动切换到仓库属性Tab
watch([() => formState.category, () => formState.ownership_type], ([newCategory, newOwnership]) => {
  const isPhysicalSelf = newCategory === 'physical' && newOwnership === 'self';
  if (!isPhysicalSelf && activeTabKey.value === 'physical') {
    activeTabKey.value = 'properties';
  }
});

// 在组件挂载时加载实体仓列表
const loadPhysicalWarehouses = async () => {
  const { items } = await getWarehouseList({ category: 'physical', page: 1, per_page: 1000 });
  physicalWarehouseOptions.value = items.map((w: Warehouse) => ({ label: w.name, value: w.id }));
};

// 表单验证规则
const rules: Record<string, any[]> = {
  code: [
    { required: true, message: '请输入仓库编码', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '编码只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入仓库名称', trigger: 'blur' }
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
      // 重置Tab状态
      activeTabKey.value = 'properties';
      
      // 加载服务商列表
      loadThirdPartyServices();
      // 加载实体仓列表（用于虚拟仓关联）
      loadPhysicalWarehouses();

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
          contact_person: props.record.contact_person || '',
          contact_phone: props.record.contact_phone || '',
          address: props.record.address || '',
          child_warehouse_ids: props.record.child_warehouse_ids || [],
          api_config: props.record.api_config,
          third_party_service_id: props.record.third_party_service_id,
          third_party_warehouse_id: props.record.third_party_warehouse_id
        });

        // 如果是三方模式，加载对应的远程仓库列表
        if (props.record.ownership_type === 'third_party' && props.record.third_party_service_id) {
           loadRemoteWarehouses(props.record.third_party_service_id);
        }

        // 设置API配置文本 (保留兼容性，虽然已隐藏)
        if (props.record.api_config) {
          apiConfigText.value = JSON.stringify(props.record.api_config, null, 2);
        } else {
          apiConfigText.value = '';
        }
      } else {
        // 创建模式，重置表单
        formRef.value?.resetFields();
        Object.assign(formState, {
          code: '',
          name: '',
          category: 'physical',
          location_type: 'domestic',
          ownership_type: 'self',
          status: 'active',
          business_type: 'standard',
          currency: 'USD',
          timezone: 'UTC',
          capacity: undefined,
          max_volume: undefined,
          contact_person: '',
          contact_phone: '',
          address: '',
          child_warehouse_ids: [],
          api_config: undefined,
          third_party_service_id: undefined,
          third_party_warehouse_id: undefined
        });
        apiConfigText.value = '';
      }
    });
  }
});

// 处理API配置
const processApiConfig = () => {
  // 新版逻辑已不再使用 apiConfigText，此处保留空函数或清理逻辑
  // 如果未来还需要存储额外配置，可以在此扩展
};

// 确定
const handleOk = async () => {
  try {
    await formRef.value?.validate();
    confirmLoading.value = true;

    // 处理API配置
    processApiConfig();

    if (props.mode === 'create') {
      await createWarehouse(formState);
      message.success('创建成功');
    } else {
      // 编辑模式：过滤掉只读字段
      const { 
        code, 
        category, 
        location_type, 
        ownership_type, 
        ...updateData 
      } = formState;

      await updateWarehouse(props.record!.id, updateData);
      message.success('更新成功');
    }

    emit('success');
    handleCancel();
  } catch (error: any) {
    message.error(error.message || '操作失败');
  } finally {
    confirmLoading.value = false;
  }
};

// 取消
const handleCancel = () => {
  emit('update:visible', false);
};
</script>

<style scoped>
.warehouse-modal-tabs {
  margin-top: -16px;
}

.tab-content {
  padding: 16px 0;
  max-height: 500px;
  overflow-y: auto;
}

.conditional-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.section-title {
  font-weight: 600;
  margin-bottom: 16px;
  color: #1890ff;
  font-size: 14px;
}

.text-gray-500 {
  color: #666;
}

.text-xs {
  font-size: 12px;
}

.mt-1 {
  margin-top: 4px;
}

.mb-4 {
  margin-bottom: 16px;
}

.py-8 {
  padding-top: 32px;
  padding-bottom: 32px;
}

.text-center {
  text-align: center;
}

.text-lg {
  font-size: 16px;
}

.text-gray-400 {
  color: #999;
}

.flex {
  display: flex;
}

.gap-2 {
  gap: 8px;
}

.flex-1 {
  flex: 1;
}
</style>
