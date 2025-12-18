<script setup lang="ts">
import { Descriptions, Table, Input, InputNumber, DatePicker, Select, Textarea } from 'ant-design-vue';
import { type TaxCustomsDeclaration } from '#/api/customs/declaration';
import { getUnitName } from '../declaration.config';
import { type DictItem } from '#/api/system/dict';

defineProps<{
  detail: TaxCustomsDeclaration;
  infoConfig: any[];
  columns: any[];
  isEditMode?: boolean;
  transactionModeOptions?: DictItem[];
  consigneeOptions?: { label: string; value: string }[];
}>();
</script>

<template>
  <div class="p-4">
    <!-- 表头信息区 - 支持编辑 -->
    <Descriptions bordered size="small" :column="4" class="mb-6 custom-descriptions">
      <Descriptions.Item v-for="(item, index) in infoConfig" :key="index" :label="item.label" :span="item.span">
        <!-- 合同号 -->
        <div v-if="item.label.includes('Contract No')">
          <Input 
            v-if="isEditMode"
            v-model:value="detail.contract_no"
            size="small"
            placeholder="合同号"
          />
          <span v-else>{{ item.value }}</span>
        </div>
        
        <!-- 日期 -->
        <div v-else-if="item.label.includes('Date')">
          <DatePicker 
            v-if="isEditMode"
            v-model:value="detail.export_date"
            size="small"
            class="w-full"
            value-format="YYYY-MM-DD"
          />
          <span v-else>{{ item.value }}</span>
        </div>
        
        <!-- 成交方式 -->
        <div v-else-if="item.label.includes('Trade Term')">
          <Select 
            v-if="isEditMode && transactionModeOptions"
            v-model:value="detail.transaction_mode"
            size="small"
            class="w-full"
            show-search
            :options="transactionModeOptions"
            placeholder="请选择"
          />
          <span v-else>{{ item.value }}</span>
        </div>
        
        <!-- 买方 -->
        <div v-else-if="item.label.includes('Buyers') && !item.label.includes('TEL') && !item.label.includes('FAX') && !item.label.includes('Address')">
          <Select 
            v-if="isEditMode && consigneeOptions"
            v-model:value="detail.overseas_consignee"
            size="small"
            class="w-full"
            show-search
            :options="consigneeOptions"
            placeholder="请选择收货人"
          />
          <span v-else>{{ item.value }}</span>
        </div>
        
        <!-- 其他字段只读显示 -->
        <div v-else class="px-1 min-h-[22px] flex items-center">
          {{ item.value }}
        </div>
      </Descriptions.Item>
      
      <!-- 合同条款 - 可编辑 -->
      <Descriptions.Item label="合同条款" :span="4">
        <Textarea 
          v-if="isEditMode"
          v-model:value="detail.documents"
          size="small"
          :auto-size="{ minRows: 2, maxRows: 4 }"
          placeholder="请输入合同条款"
        />
        <span v-else>{{ detail.documents || '-' }}</span>
      </Descriptions.Item>
    </Descriptions>
    
    <!-- 商品明细表 - 支持编辑 -->
    <Table 
      :columns="columns" 
      :dataSource="detail.items" 
      rowKey="id" 
      :pagination="false" 
      size="small" 
      bordered 
    >
      <template #bodyCell="{ column, record }">
        <!-- 货物名称 -->
        <template v-if="column.dataIndex === 'product_name_spec'">
          <Input 
            v-if="isEditMode" 
            :value="record.product_name_spec?.split('|')[0]" 
            @update:value="(val: any) => {
              const spec = record.product_name_spec?.split('|')[1] || '';
              record.product_name_spec = `${val}|${spec}`;
            }"
            size="small" 
          />
          <span v-else>{{ record.product_name_spec?.split('|')[0] }}</span>
        </template>

        <!-- HS编码 -->
        <template v-if="column.dataIndex === 'hs_code'">
          <Input 
            v-if="isEditMode" 
            v-model:value="record.hs_code" 
            size="small" 
          />
          <span v-else>{{ record.hs_code }}</span>
        </template>

        <!-- 数量及单位 -->
        <template v-if="column.dataIndex === 'qty_unit'">
          <span v-if="!isEditMode">
            {{ record.qty }}{{ getUnitName(record.unit) }}
          </span>
        </template>

        <!-- 单价 -->
        <template v-if="column.dataIndex === 'usd_unit_price'">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="record.usd_unit_price" 
            size="small" 
            :min="0"
            :precision="4"
            class="w-full"
          />
          <span v-else>{{ record.usd_unit_price }}</span>
        </template>

        <!-- 总金额 -->
        <template v-if="column.dataIndex === 'usd_total'">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="record.usd_total" 
            size="small" 
            :min="0"
            :precision="2"
            class="w-full"
          />
          <span v-else>{{ record.usd_total }}</span>
        </template>
      </template>
    </Table>
  </div>
</template>

