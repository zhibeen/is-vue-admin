<script setup lang="ts">
import { useVbenModal } from '@vben/common-ui';
import { useVbenForm } from '#/adapter/form';
import { createManualContract } from '#/api/serc/supply';
import { getSupplierList } from '#/api/purchase/supplier';
import { getSkuListApi } from '#/api/core/product';
import { getCompanyList } from '#/api/serc/foundation';
import { getPaymentTerms } from '#/api/serc/finance';
import { message, Select, InputNumber, Button, Table, Popconfirm, Card, Input } from 'ant-design-vue';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { onMounted, ref, reactive } from 'vue';

const emit = defineEmits(['success']);

const supplierOptions = ref<any[]>([]);
const companyOptions = ref<any[]>([]);
const productOptions = ref<any[]>([]);
const paymentTermOptions = ref<any[]>([]);

// 1. 定义默认付款方式常量
const DEFAULT_PAYMENT_METHOD = 'T/T';

// --- Form Schema (Header Only) ---
const [Form, formApi] = useVbenForm({
  wrapperClass: 'grid-cols-12 gap-4', 
  commonConfig: {
    labelWidth: 80,
  },
  schema: [
    {
      component: 'Select',
      fieldName: 'company_id',
      label: '采购主体',
      rules: 'required',
      formItemClass: 'col-span-6',
      componentProps: {
        options: companyOptions,
        fieldNames: { label: 'legal_name', value: 'id' },
        showSearch: true,
        optionFilterProp: 'label',
        class: 'w-full',
        placeholder: '请选择我方主体',
      },
    },
    {
      component: 'Select',
      fieldName: 'supplier_id',
      label: '供应商',
      rules: 'required',
      formItemClass: 'col-span-6',
      componentProps: {
        options: supplierOptions,
        fieldNames: { label: 'name', value: 'id' },
        showSearch: true,
        optionFilterProp: 'label',
        class: 'w-full',
        placeholder: '请选择供应商',
        onChange: (val: any) => handleSupplierChange(val),
      },
    },
    {
      component: 'DatePicker',
      fieldName: 'event_date',
      label: '业务日期',
      rules: 'required',
      defaultValue: new Date().toISOString().split('T')[0],
      formItemClass: 'col-span-6', // Use formItemClass
      componentProps: {
        valueFormat: 'YYYY-MM-DD',
        class: 'w-full',
        placeholder: '请选择日期',
      },
    },
    {
      component: 'Select',
      fieldName: 'currency',
      label: '币种',
      defaultValue: 'CNY',
      formItemClass: 'col-span-6', // Use formItemClass
      componentProps: {
        options: [
          { label: 'CNY', value: 'CNY' },
          { label: 'USD', value: 'USD' },
        ],
        class: 'w-full',
      },
    },
    {
      component: 'Input',
      fieldName: 'delivery_address',
      label: '交付地点',
      formItemClass: 'col-span-6',
      componentProps: { placeholder: '请输入交付地点' },
    },
    {
      component: 'DatePicker',
      fieldName: 'delivery_date',
      label: '送货日期',
      formItemClass: 'col-span-6',
      componentProps: { 
        valueFormat: 'YYYY-MM-DD',
        class: 'w-full', 
        placeholder: '请选择送货日期' 
      },
    },
    {
      component: 'Textarea',
      fieldName: 'notes',
      label: '合同备注',
      formItemClass: 'col-span-12',
      componentProps: { rows: 2, placeholder: '请输入合同备注' },
    },
    {
      component: 'Divider',
      fieldName: 'divider2',
      label: '财务信息',
      formItemClass: 'col-span-12',
      componentProps: { orientation: 'left', plain: true },
    },
    {
      component: 'Select',
      fieldName: 'payment_term_id',
      label: '付款条款',
      // helpMessage: '留空将使用供应商默认条款', // 移除不支持的属性
      formItemClass: 'col-span-6',
      componentProps: {
        options: paymentTermOptions,
        fieldNames: { label: 'name', value: 'id' },
        placeholder: '例如: 月结30天 / 预付30% (留空使用默认)',
        allowClear: true,
      },
    },
    {
      component: 'Select',
      fieldName: 'payment_method',
      label: '付款方式',
      defaultValue: DEFAULT_PAYMENT_METHOD,
      formItemClass: 'col-span-6',
      // helpMessage: '留空将使用供应商默认方式', // 移除不支持的属性
      componentProps: {
        options: [
          { label: '银行转账 (T/T)', value: 'T/T' },
          { label: '信用证 (L/C)', value: 'L/C' },
          { label: '承兑汇票', value: 'Draft' },
          { label: '现金 (Cash)', value: 'Cash' },
          { label: '支票 (Check)', value: 'Check' },
        ],
        allowClear: true,
        placeholder: '请选择付款方式',
      },
    },
  ],
});

// 2. 处理供应商变更，自动回填付款条款
function handleSupplierChange(supplierId: number) {
  if (!supplierId) return;
  
  const supplier = supplierOptions.value.find(item => item.id === supplierId);
  if (supplier) {
    const valuesToSet: any = {};
    
    // 优先使用结构化的 payment_term_id
    if (supplier.payment_term_id) {
        valuesToSet.payment_term_id = supplier.payment_term_id;
        // 查找条款名称用于提示
        const term = paymentTermOptions.value.find(t => t.id === supplier.payment_term_id);
        if (term) {
            message.info(`已应用供应商默认条款: ${term.name}`);
        }
    } else if (supplier.payment_terms) {
        // 兼容旧文本字段 (仅提示，无法自动对应 Select ID，除非完全匹配)
        message.info(`供应商默认条款(文本): ${supplier.payment_terms}，请手动选择对应项`);
    }
    
    formApi.setValues(valuesToSet);
  }
}

// --- Items Logic ---
const items = ref<any[]>([]);
const newItem = reactive({
  selected_sku: undefined as string | undefined,
  confirmed_qty: 1,
  unit_price: 0,
  notes: '',
});

// Table Columns
const columns: any[] = [ // Explicitly type columns as any[] to bypass strict type checking for 'align'
  { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 120 },
  { title: '特征码', dataIndex: 'feature_code', key: 'feature_code', width: 180, ellipsis: true }, // Added Feature Code
  { title: '商品名称', dataIndex: 'product_name', key: 'product_name', width: 180, ellipsis: true },
  { title: '数量', dataIndex: 'confirmed_qty', key: 'confirmed_qty', width: 100, align: 'center' }, // Editable
  { title: '单价(含税)', dataIndex: 'unit_price', key: 'unit_price', width: 120, align: 'right' }, // Editable
  { title: '金额(含税)', key: 'total', width: 120, align: 'right', customRender: ({ record }: any) => `￥${(record.confirmed_qty * record.unit_price).toFixed(2)}` },
  { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true }, // Editable
  { title: '操作', key: 'action', width: 60, align: 'center' },
];

function addItem() {
  if (!newItem.selected_sku) {
    message.warning('请选择商品');
    return;
  }
  if (newItem.confirmed_qty <= 0) {
    message.warning('数量必须大于0');
    return;
  }
  
  const product = productOptions.value.find(p => p.value === newItem.selected_sku);
  
  // 检查是否已添加相同的 SKU
  if (items.value.some(item => item.sku === newItem.selected_sku)) {
      message.warning('该SKU已添加');
      return;
  }
  
  items.value.push({
    product_id: product?.raw?.product_id, // 传递 SPU ID 给后端 (暂时的兼容方案)
    // 修复: 现在使用的是 getSkuListApi，返回的是 Variant 对象 (ProductVariants表)
    // 直接获取 sku 和 feature_code
    sku: product?.raw?.sku || 'Unknown', 
    feature_code: product?.raw?.feature_code || '-',
    product_name: product?.raw?.product_name || 'Unknown',
    confirmed_qty: newItem.confirmed_qty,
    unit_price: newItem.unit_price,
    notes: newItem.notes,
  });
  
  // Reset
  newItem.selected_sku = undefined;
  newItem.confirmed_qty = 1;
  newItem.unit_price = 0;
  newItem.notes = '';
}

function removeItem(index: number) {
  items.value.splice(index, 1);
}

// --- Modal ---
const [Modal, modalApi] = useVbenModal({
  title: '录入交付合同',
  class: 'w-[1000px]',
  draggable: true,
  onConfirm: async () => {
    try {
      // Validate and get values
      await formApi.validate();
      const values = await formApi.getValues() as any;
      
      console.log('Form Values (getValues):', values);

      if (items.value.length === 0) {
        message.error('请至少添加一行商品明细');
        return;
      }
      
      const payloadItems = items.value.map(item => ({
        product_id: item.product_id,
        confirmed_qty: item.confirmed_qty,
        unit_price: item.unit_price,
        notes: item.notes,
      }));
      
      const payload = {
        supplier_id: values.supplier_id,
        company_id: values.company_id,
        currency: values.currency,
        event_date: values.event_date,
        delivery_address: values.delivery_address,
        delivery_date: values.delivery_date,
        notes: values.notes,
        payment_term_id: values.payment_term_id,
        payment_method: values.payment_method,
        items: payloadItems,
      };
      console.log('Submitting Contract Payload:', payload);

      await createManualContract(payload);
      
      message.success('合同创建成功');
      emit('success');
      modalApi.close();
      items.value = [];
    } catch (e) {
      console.error(e);
    }
  },
});

// --- Init ---
onMounted(async () => {
  try {
      const [supplierRes, companyRes, productRes, termsRes] = await Promise.all([
        getSupplierList(),
        getCompanyList(),
        // 切换为查询 SKU 变体接口，以获取准确的 sku 和 feature_code
        getSkuListApi({ page: 1, per_page: 5000 }),
        getPaymentTerms()
      ]);
      
      supplierOptions.value = supplierRes.items || [];
      companyOptions.value = companyRes || []; 
      paymentTermOptions.value = termsRes || []; 
      
      // 映射 SKU 数据
      productOptions.value = (productRes.items || []).map((p: any) => ({
          label: `${p.product_name} (${p.sku})`, // 显示: 产品名 (SKU)
          value: p.sku, // 使用 SKU 作为唯一标识 (Value)
          key: p.sku, // 使用 SKU 作为唯一键
          raw: p 
      }));
  } catch (error) {
      console.error("Failed to load initial data", error);
  }
});

// Filter function for Select
const filterOption = (input: string, option: any) => {
  const product = option.raw;
  const searchStr = input.toLowerCase();
  
  // 优化搜索：同时匹配 SKU、名称和特征码
  const nameMatch = product.product_name?.toLowerCase().includes(searchStr);
  const skuMatch = product.sku?.toLowerCase().includes(searchStr);
  const featureMatch = product.feature_code?.toLowerCase().includes(searchStr);
  
  return nameMatch || skuMatch || featureMatch;
};
</script>

<template>
  <Modal>
    <div class="flex flex-col gap-4 p-1">
      <!-- Header Section -->
      <Card size="small" title="基本信息" :bordered="false" class="shadow-sm">
        <Form />
      </Card>
      
      <!-- Items Section -->
      <Card size="small" title="商品明细" :bordered="false" class="shadow-sm flex-1">
        <template #extra>
            <div class="text-xs text-gray-400">
                已添加 {{ items.length }} 项商品
            </div>
        </template>
        
        <!-- Add Item Row -->
        <div class="flex gap-3 items-center mb-4 p-3 bg-gray-50 rounded border border-dashed border-gray-200">
            <Select
              v-model:value="newItem.selected_sku"
              :options="productOptions"
              show-search
              :filter-option="filterOption"
              placeholder="请搜索并选择商品 (名称/SKU)"
              class="flex-[2]"
            />
            <InputNumber
              v-model:value="newItem.confirmed_qty"
              :min="1"
              placeholder="数量"
              class="w-20"
            />
            <InputNumber
              v-model:value="newItem.unit_price"
              :min="0"
              :precision="2"
              placeholder="含税单价"
              class="w-28"
            >
              <template #addonBefore>￥</template>
            </InputNumber>
            <Input
              v-model:value="newItem.notes"
              placeholder="备注 (选填)"
              class="flex-1"
            />
            <Button type="primary" ghost @click="addItem">
                <template #icon><PlusOutlined /></template>
                添加
            </Button>
        </div>

        <!-- Table -->
        <Table 
          :columns="columns" 
          :data-source="items" 
          size="small" 
          :pagination="false"
          row-key="sku" 
          bordered
        >
          <!-- Editable Columns using slots -->
          <template #bodyCell="{ column, record, index }">
            <!-- Quantity -->
            <template v-if="column.key === 'confirmed_qty'">
                <InputNumber v-model:value="record.confirmed_qty" :min="1" size="small" class="w-full text-center" :bordered="false" />
            </template>
            
            <!-- Unit Price -->
            <template v-else-if="column.key === 'unit_price'">
                <InputNumber v-model:value="record.unit_price" :min="0" :precision="2" size="small" class="w-full text-right" :bordered="false">
                    <template #addonBefore>￥</template>
                </InputNumber>
            </template>
            
            <!-- Notes -->
            <template v-else-if="column.key === 'notes'">
                <Input v-model:value="record.notes" size="small" :bordered="false" placeholder="无" />
            </template>

            <!-- Action -->
            <template v-else-if="column.key === 'action'">
              <Popconfirm title="确定移除此商品?" @confirm="removeItem(index)">
                 <Button type="text" danger size="small">
                   <DeleteOutlined />
                 </Button>
              </Popconfirm>
            </template>
          </template>
          
          <!-- Summary Row -->
          <template #summary>
              <Table.Summary.Row>
                  <Table.Summary.Cell :index="0" :col-span="4" class="text-right font-bold">
                      合计:
                  </Table.Summary.Cell>
                  <Table.Summary.Cell :index="1" class="text-right font-bold text-primary">
                      ￥{{ items.reduce((sum, item) => sum + (item.confirmed_qty * item.unit_price), 0).toFixed(2) }}
                  </Table.Summary.Cell>
                  <Table.Summary.Cell :index="2" :col-span="2" />
              </Table.Summary.Row>
          </template>
        </Table>
      </Card>
    </div>
  </Modal>
</template>

<style scoped>
:deep(.ant-card-head) {
    min-height: 40px;
    padding: 0 12px;
}
:deep(.ant-card-body) {
    padding: 12px;
}
/* Remove border for cleaner edit look */
:deep(.ant-input-number-group-addon) {
    border: none;
    background: transparent;
}
</style>
