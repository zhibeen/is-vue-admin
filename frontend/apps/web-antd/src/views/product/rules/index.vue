<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Card, Table, Button, Modal, Form, Input, Switch, message, Select, Tag, Divider } from 'ant-design-vue';
import { EditOutlined } from '@ant-design/icons-vue';
import { getProductRulesApi, updateProductRuleApi, type ProductBusinessRule } from '#/api/core/product-rule';

const rules = ref<ProductBusinessRule[]>([]);
const loading = ref(false);
const modalVisible = ref(false);
const formRef = ref();
const formState = ref<Partial<ProductBusinessRule>>({});

const columns = [
  { title: '业务类型', dataIndex: 'name', key: 'name' },
  { title: '代码', dataIndex: 'business_type', key: 'business_type' },
  { title: '生成策略', key: 'generate_strategy' },
  { title: '审核要求', key: 'requires_audit' },
  { title: '操作', key: 'action', width: 100 },
];

const strategyOptions = [
  { label: '汽配标准 (Vehicle Standard)', value: 'vehicle' },
  { label: '通用简易 (General Simple)', value: 'general' },
  { label: '电子产品 (Electronics)', value: 'electronics' }, // Example
  { label: '自定义 (Custom)', value: 'custom' },
];

onMounted(() => {
  loadData();
});

async function loadData() {
  loading.value = true;
  try {
    rules.value = await getProductRulesApi();
  } catch (e) {
    message.error('加载规则失败');
  } finally {
    loading.value = false;
  }
}

function handleEdit(record: ProductBusinessRule) {
  formState.value = { ...record };
  modalVisible.value = true;
}

async function handleSave() {
  try {
    await formRef.value.validate();
    if (formState.value.id) {
      await updateProductRuleApi(formState.value.id, formState.value);
      message.success('更新成功');
      modalVisible.value = false;
      loadData();
    }
  } catch (e) {
    console.error(e);
  }
}
</script>

<template>
  <Page title="业务规则配置">
    <div class="p-4">
      <Card :bordered="false">
        <Table
          :columns="columns"
          :data-source="rules"
          :loading="loading"
          row-key="id"
          size="middle"
          :pagination="false"
        >
           <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'generate_strategy'">
                  <Tag color="blue" v-if="record.generate_strategy === 'vehicle'">汽配标准</Tag>
                  <Tag color="cyan" v-else-if="record.generate_strategy === 'general'">通用简易</Tag>
                  <Tag v-else>{{ record.generate_strategy }}</Tag>
              </template>
              <template v-if="column.key === 'requires_audit'">
                  <Tag :color="record.requires_audit ? 'orange' : 'green'">
                      {{ record.requires_audit ? '需要审核' : '免审' }}
                  </Tag>
              </template>
              <template v-if="column.key === 'action'">
                  <Button type="link" size="small" @click="handleEdit(record)">
                      <EditOutlined /> 配置
                  </Button>
              </template>
           </template>
        </Table>
      </Card>

      <Modal
        v-model:open="modalVisible"
        title="配置业务规则"
        @ok="handleSave"
      >
        <Form
            ref="formRef"
            :model="formState"
            layout="vertical"
            class="pt-4"
        >
            <Form.Item label="业务名称">
                <Input v-model:value="formState.name" disabled />
            </Form.Item>
            
            <Divider orientation="left">编码生成规则</Divider>
            
            <Form.Item label="生成策略" name="generate_strategy" :rules="[{ required: true }]">
                <Select v-model:value="formState.generate_strategy">
                    <Select.Option v-for="opt in strategyOptions" :key="opt.value" :value="opt.value">
                        {{ opt.label }}
                    </Select.Option>
                </Select>
            </Form.Item>
            
            <Form.Item label="默认前缀" name="sku_prefix" tooltip="可选，如配置则所有该类型产品SKU都会带上前缀">
                <Input v-model:value="formState.sku_prefix" placeholder="例如：V-" />
            </Form.Item>
            
            <Divider orientation="left">流程控制</Divider>
            
            <Form.Item label="创建审核" name="requires_audit" tooltip="开启后，新建产品必须经过审核才能上架">
                 <Switch v-model:checked="formState.requires_audit" checked-children="开启" un-checked-children="关闭" />
            </Form.Item>
        </Form>
      </Modal>
    </div>
  </Page>
</template>

