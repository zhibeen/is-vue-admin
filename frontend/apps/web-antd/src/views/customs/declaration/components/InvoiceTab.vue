<script setup lang="ts">
import { Descriptions, Table, Input, InputNumber, DatePicker, Select, Textarea } from 'ant-design-vue';
import { type TaxCustomsDeclaration } from '#/api/customs/declaration';
import { getUnitName } from '../declaration.config';
import { type DictItem } from '#/api/system/dict';

defineProps<{
  detail: TaxCustomsDeclaration;
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
      <!-- 发票编号 (使用合同号) -->
      <Descriptions.Item label="编号 NO" :span="2">
        <Input 
          v-if="isEditMode"
          v-model:value="detail.contract_no"
          size="small"
          placeholder="发票编号"
        />
        <span v-else>{{ detail.contract_no || '20251112A' }}</span>
      </Descriptions.Item>
      
      <!-- 境外收货人 -->
      <Descriptions.Item label="商号 Sold to Massrs" :span="2">
        <Select 
          v-if="isEditMode && consigneeOptions"
          v-model:value="detail.overseas_consignee"
          size="small"
          class="w-full"
          show-search
          :options="consigneeOptions"
          placeholder="请选择收货人"
        />
        <span v-else>{{ detail.overseas_consignee }}</span>
      </Descriptions.Item>
      
      <!-- 出口日期 -->
      <Descriptions.Item label="日期 DATE" :span="1">
        <DatePicker 
          v-if="isEditMode"
          v-model:value="detail.export_date"
          size="small"
          class="w-full"
          value-format="YYYY-MM-DD"
        />
        <span v-else>{{ detail.export_date }}</span>
      </Descriptions.Item>
      
      <!-- 成交方式 -->
      <Descriptions.Item label="成交方式 Transaction method" :span="1">
        <Select 
          v-if="isEditMode && transactionModeOptions"
          v-model:value="detail.transaction_mode"
          size="small"
          class="w-full"
          show-search
          :options="transactionModeOptions"
          placeholder="请选择"
        />
        <span v-else>{{ detail.transaction_mode || 'CIF' }}</span>
      </Descriptions.Item>
      
      <!-- 唛头 -->
      <Descriptions.Item label="唛头 Marks" :span="2">
        <Input 
          v-if="isEditMode"
          v-model:value="detail.marks_and_notes"
          size="small"
          placeholder="唛头信息"
        />
        <span v-else>{{ detail.marks_and_notes || '宁波华瑞逸德电子商务有限公司' }}</span>
      </Descriptions.Item>
      
      <!-- 备注 -->
      <Descriptions.Item label="备注" :span="4">
        <Textarea 
          v-if="isEditMode"
          v-model:value="detail.documents"
          size="small"
          :auto-size="{ minRows: 1, maxRows: 3 }"
          placeholder="备注信息"
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
    
    <!-- 总计行 - 支持编辑 -->
    <div class="mt-4 text-right pr-12 text-sm text-foreground">
      <span class="mr-4 font-bold">大写: 叁万肆仟零肆美元伍角叁分肆厘</span>
      <span class="font-bold">小写: $
        <InputNumber 
          v-if="isEditMode" 
          v-model:value="detail.fob_total" 
          size="small" 
          :min="0"
          :precision="2"
          class="w-32"
        />
        <span v-else>{{ detail.fob_total }}</span>
      </span>
    </div>
  </div>
</template>

