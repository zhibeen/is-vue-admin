<template>
  <a-modal
    v-model:visible="visible"
    :title="`管理SKU - 分组ID: ${groupId}`"
    width="800px"
    :confirm-loading="confirmLoading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <div class="mb-4">
      <a-alert
        message="SKU管理说明"
        description="在此分组中添加或移除SKU，这些SKU将作为一个整体参与库存分配策略"
        type="info"
        show-icon
      />
    </div>

    <div class="flex gap-4 mb-4">
      <div class="flex-1">
        <a-card title="添加SKU" size="small">
          <a-form
            ref="addFormRef"
            :model="addFormState"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 16 }"
            :rules="addRules"
          >
            <a-form-item label="SKU" name="sku">
              <a-input
                v-model:value="addFormState.sku"
                placeholder="请输入SKU"
                @press-enter="handleAddSku"
              />
            </a-form-item>
            <a-form-item :wrapper-col="{ offset: 6, span: 16 }">
              <a-button type="primary" @click="handleAddSku" :loading="addingSku">
                添加
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </div>

      <div class="flex-1">
        <a-card title="批量导入" size="small">
          <div class="mb-2">
            <a-textarea
              v-model:value="batchSkus"
              placeholder="每行输入一个SKU，支持批量导入"
              :rows="4"
            />
          </div>
          <a-button type="primary" @click="handleBatchAdd" :loading="batchAdding">
            批量导入
          </a-button>
          <div class="text-gray-500 text-xs mt-2">
            每行一个SKU，自动去重
          </div>
        </a-card>
      </div>
    </div>

    <a-card title="分组中的SKU列表">
      <template #extra>
        <a-space>
          <a-input-search
            v-model:value="searchSku"
            placeholder="搜索SKU"
            style="width: 200px"
            @search="handleSearchSku"
          />
          <a-button size="small" @click="handleRefreshSkus">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>

      <div class="bg-white">
        <VbenVxeGrid ref="skuGridRef" :grid-options="skuGridOptions" />
      </div>
    </a-card>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue';
import type { FormInstance } from 'ant-design-vue';
import { message, Modal } from 'ant-design-vue';
import { VbenVxeGrid } from '#/adapter/vxe-table';
import { ReloadOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { getGroupSkuList, addSkuToGroup, removeSkuFromGroup, type ProductGroupItem } from '#/api/virtual';
import type { VxeGridProps, VxeGridInstance } from '#/adapter/vxe-table';

interface Props {
  visible: boolean;
  groupId: number;
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  groupId: 0
});

const emit = defineEmits<Emits>();

const addFormRef = ref<FormInstance>();
const skuGridRef = ref<VxeGridInstance>();
const confirmLoading = ref(false);
const addingSku = ref(false);
const batchAdding = ref(false);
const searchSku = ref('');
const batchSkus = ref('');

// 添加SKU表单
const addFormState = reactive({
  sku: ''
});

// 表单验证规则
const addRules = {
  sku: [
    { required: true, message: '请输入SKU', trigger: 'blur' }
  ]
};

// SKU表格配置
const skuGridOptions = reactive<VxeGridProps>({
  border: true,
  stripe: true,
  showOverflow: true,
  keepSource: true,
  height: '300',
  columns: [
    { type: 'seq', width: 60, title: '序号' },
    { field: 'sku', title: 'SKU', width: 150 },
    {
      title: '操作',
      width: 100,
      fixed: 'right',
      slots: {
        default: ({ row }: { row: ProductGroupItem }) => {
          return (
            <a-button
              type="link"
              size="small"
              danger
              onClick={() => handleRemoveSku(row.sku)}
            >
              <DeleteOutlined /> 移除
            </a-button>
          );
        }
      }
    }
  ],
  data: [],
  pagerConfig: {
    enabled: true,
    pageSize: 10,
    pageSizes: [10, 20, 50],
    layouts: ['PrevJump', 'PrevPage', 'Number', 'NextPage', 'NextJump', 'Sizes', 'Total']
  },
  toolbarConfig: {
    refresh: { code: 'query' },
    custom: true
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        try {
          const params = {
            page: page.currentPage,
            per_page: page.pageSize,
            q: searchSku.value || undefined
          };
          const res = await getGroupSkuList(props.groupId, params);
          return {
            result: res.items,
            page: { total: res.total }
          };
        } catch (error) {
          console.error('获取SKU列表失败:', error);
          message.error('获取SKU列表失败');
          return { result: [], page: { total: 0 } };
        }
      }
    }
  }
});

// 加载SKU列表
const loadSkus = () => {
  skuGridRef.value?.commitProxy('query');
};

// 搜索SKU
const handleSearchSku = () => {
  loadSkus();
};

// 刷新SKU列表
const handleRefreshSkus = () => {
  searchSku.value = '';
  loadSkus();
};

// 添加SKU
const handleAddSku = async () => {
  try {
    await addFormRef.value?.validate();
    addingSku.value = true;

    // TODO: 调用添加SKU API
    // await addSkuToGroup(props.groupId, { sku: addFormState.sku });
    message.success('添加成功');

    // 清空表单并刷新列表
    addFormState.sku = '';
    loadSkus();
  } catch (error) {
    console.error('添加SKU失败:', error);
  } finally {
    addingSku.value = false;
  }
};

// 批量添加SKU
const handleBatchAdd = async () => {
  if (!batchSkus.value.trim()) {
    message.warning('请输入SKU列表');
    return;
  }

  batchAdding.value = true;
  try {
    const skus = batchSkus.value
      .split('\n')
      .map(sku => sku.trim())
      .filter(sku => sku.length > 0);

    // 去重
    const uniqueSkus = [...new Set(skus)];

    // TODO: 批量添加SKU
    // for (const sku of uniqueSkus) {
    //   await addSkuToGroup(props.groupId, { sku });
    // }

    message.success(`成功导入 ${uniqueSkus.length} 个SKU`);
    batchSkus.value = '';
    loadSkus();
  } catch (error) {
    console.error('批量导入失败:', error);
    message.error('批量导入失败');
  } finally {
    batchAdding.value = false;
  }
};

// 移除SKU
const handleRemoveSku = (sku: string) => {
  Modal.confirm({
    title: '确认移除',
    content: `确定要从分组中移除SKU "${sku}" 吗？`,
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        // TODO: 调用移除SKU API
        // await removeSkuFromGroup(props.groupId, sku);
        message.success('移除成功');
        loadSkus();
      } catch (error) {
        console.error('移除失败:', error);
        message.error('移除失败');
      }
    }
  });
};

// 确定
const handleOk = () => {
  emit('success');
  handleCancel();
};

// 取消
const handleCancel = () => {
  emit('update:visible', false);
};

// 监听 visible 变化
watch(() => props.visible, (val) => {
  if (val && props.groupId) {
    nextTick(() => {
      loadSkus();
      addFormState.sku = '';
      batchSkus.value = '';
      searchSku.value = '';
    });
  }
});
</script>
