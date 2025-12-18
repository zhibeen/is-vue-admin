<script setup lang="ts">
import { Descriptions, Table, Input, Select, DatePicker, InputNumber } from 'ant-design-vue';
import { type TaxCustomsDeclaration } from '#/api/customs/declaration';
import { getUnitName, UNIT_MAP } from '../declaration.config';
import { type DictItem } from '#/api/system/dict';
import type { SysCompany } from '#/api/serc/model';

defineProps<{
  detail: TaxCustomsDeclaration;
  isEditMode: boolean;
  formItems: any[];
  columns: any[];
  // Options
  countryOptions: DictItem[];
  portOptions: DictItem[];
  transactionModeOptions: DictItem[];
  tradeModeOptions: DictItem[];
  natureOfExemptionOptions: DictItem[];
  transportModeOptions: DictItem[];
  companyOptions: SysCompany[];
  // Methods
  calculateFobUnitPrice: (item: any, header: TaxCustomsDeclaration) => string;
}>();
</script>

<template>
  <div class="p-4">
    <Descriptions 
      bordered 
      size="small" 
      :column="4" 
      class="mb-6 custom-descriptions"
    >
      <Descriptions.Item v-for="(item, index) in formItems" :key="index" :label="item.label" :span="item.span">
        <div v-if="isEditMode && item.key">
          <!-- 日期类型 -->
          <DatePicker 
            v-if="['export_date', 'declare_date'].includes(item.key)"
            v-model:value="(detail as any)[item.key]"
            size="small"
            class="w-full"
            value-format="YYYY-MM-DD"
          />
          
          <!-- 成交方式 Select (仅选择) -->
          <Select
            v-else-if="item.key === 'transaction_mode'"
            v-model:value="(detail as any)[item.key]"
            size="small"
            class="w-full"
            show-search
            :options="transactionModeOptions"
            placeholder="请选择"
          />

          <!-- 监管方式 Select -->
          <Select
            v-else-if="item.key === 'trade_mode'"
            v-model:value="(detail as any)[item.key]"
            size="small"
            class="w-full"
            show-search
            :options="tradeModeOptions"
            placeholder="请选择"
          />

          <!-- 征免性质 Select -->
          <Select
            v-else-if="item.key === 'nature_of_exemption'"
            v-model:value="(detail as any)[item.key]"
            size="small"
            class="w-full"
            show-search
            :options="natureOfExemptionOptions"
            placeholder="请选择"
          />

          <!-- 运输方式 Select -->
          <Select
            v-else-if="item.key === 'transport_mode'"
            v-model:value="(detail as any)[item.key]"
            size="small"
            class="w-full"
            show-search
            :options="transportModeOptions"
          />

          <!-- 贸易国/运抵国 Select (字典联动) -->
          <Select
            v-else-if="['trade_country', 'destination_country'].includes(item.key!)"
            v-model:value="(detail as any)[item.key!]"
            size="small"
            class="w-full"
            show-search
            :options="countryOptions"
            placeholder="请选择"
          />

          <!-- 港口/口岸 Select (字典联动) -->
          <Select
            v-else-if="['loading_port', 'entry_port', 'departure_port'].includes(item.key!)"
            v-model:value="(detail as any)[item.key!]"
            size="small"
            class="w-full"
            show-search
            :options="portOptions"
            placeholder="请选择"
          />

          <!-- 默认 Input -->
          <Input 
            v-else
            v-model:value="(detail as any)[item.key]" 
            size="small" 
            allow-clear
            :placeholder="'请输入' + item.label"
            class="!bg-white dark:!bg-gray-800 !border !border-blue-200 dark:!border-blue-800 focus:!border-blue-500 !rounded-sm"
          />
        </div>
        <div v-else class="px-1 min-h-[22px] flex items-center">
          {{ item.value }}
        </div>
      </Descriptions.Item>
    </Descriptions>
    <Table 
      :columns="columns" 
      :dataSource="detail.items" 
      rowKey="id" 
      :pagination="false" 
      size="small" 
      bordered 
      :scroll="{ x: 1500 }" 
    >
      <template #bodyCell="{ column, record }">
        <!-- 1. 商品编号 HS Code -->
        <template v-if="column.dataIndex === 'hs_code'">
          <Input v-if="isEditMode" v-model:value="record.hs_code" size="small" />
          <span v-else>{{ record.hs_code }}</span>
        </template>

        <!-- 2. 商品名称 Product Name -->
        <template v-if="column.dataIndex === 'product_name'">
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

        <!-- 3. 规格型号 Spec -->
        <template v-if="column.dataIndex === 'product_spec'">
          <Input 
            v-if="isEditMode" 
            :value="record.product_name_spec?.split('|')[1] || ''" 
            @update:value="(val: any) => {
              const name = record.product_name_spec?.split('|')[0] || '';
              record.product_name_spec = `${name}|${val}`;
            }"
            size="small" 
          />
          <span v-else>{{ record.product_name_spec?.split('|')[1] || '-' }}</span>
        </template>

        <!-- 4. 数量及单位 Qty & Unit -->
        <template v-if="column.dataIndex === 'qty_unit'">
          <div v-if="isEditMode" class="flex gap-1 items-center">
            <InputNumber 
              v-model:value="record.qty" 
              size="small" 
              class="w-20" 
              placeholder="数量" 
              :precision="['007', '006', '001', '012', '011', '015', '008', '120'].includes(record.unit) ? 0 : 4"
              :min="0"
            />
            <!-- 申报单位: 下拉选择 -->
            <Select 
              v-model:value="record.unit" 
              size="small" 
              class="w-20" 
              placeholder="单位"
              :options="Object.entries(UNIT_MAP).map(([code, name]) => ({ label: name, value: code }))"
            />
          </div>
          <span v-else>
            {{ record.qty }}{{ getUnitName(record.unit) }}
          </span>
        </template>
        
        <!-- 4.1 净重 -->
        <template v-if="column.dataIndex === 'net_weight'">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="record.net_weight" 
            size="small" 
            :min="0"
            :precision="4"
          />
          <span v-else>{{ record.net_weight || '-' }}</span>
        </template>

        <!-- 4.2 毛重 -->
        <template v-if="column.dataIndex === 'gross_weight'">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="record.gross_weight" 
            size="small" 
            :min="0"
            :precision="4"
          />
          <span v-else>{{ record.gross_weight || '-' }}</span>
        </template>

        <!-- 5. 单价 USD Price -->
        <template v-if="column.dataIndex === 'usd_unit_price'">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="record.usd_unit_price" 
            size="small" 
            :min="0"
            :precision="4"
          />
          <span v-else>{{ record.usd_unit_price }}</span>
        </template>

        <!-- 6. 总价 USD Total -->
        <template v-if="column.dataIndex === 'usd_total'">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="record.usd_total" 
            size="small" 
            :min="0"
            :precision="2"
          />
          <span v-else>{{ record.usd_total }}</span>
        </template>

        <!-- 7. 币制 Currency -->
        <template v-if="column.dataIndex === 'currency'">
          <!-- 币制统一由表头控制，此处只读展示 -->
          <span class="text-gray-500">{{ detail.currency || 'USD' }}</span>
        </template>

        <!-- 8. FOB 单价 (计算字段, 不可编辑) -->
        <template v-if="column.dataIndex === 'fob_unit_price'">
          <span class="text-gray-500 text-xs">
            {{ calculateFobUnitPrice(record, detail) }}
          </span>
        </template>

        <!-- 9. 原产地 Origin -->
        <template v-if="column.dataIndex === 'origin_country'">
          <Select 
            v-if="isEditMode" 
            v-model:value="record.origin_country" 
            size="small" 
            show-search 
            :options="countryOptions"
          />
          <span v-else>{{ record.origin_country }}</span>
        </template>

        <!-- 9. 最终目的国 Dest -->
        <template v-if="column.dataIndex === 'final_dest_country'">
          <Select 
            v-if="isEditMode" 
            v-model:value="record.final_dest_country" 
            size="small" 
            show-search 
            :options="countryOptions"
          />
          <span v-else>{{ record.final_dest_country }}</span>
        </template>

        <!-- 10. 境内货源地 District -->
        <template v-if="column.dataIndex === 'district_code'">
          <Input v-if="isEditMode" v-model:value="record.district_code" size="small" />
          <span v-else>{{ record.district_code }}</span>
        </template>

        <!-- 11. 征免 Exemption -->
        <template v-if="column.dataIndex === 'exemption_way'">
          <Input v-if="isEditMode" v-model:value="record.exemption_way" size="small" />
          <span v-else>{{ record.exemption_way || '照章征税' }}</span>
        </template>

      </template>
    </Table>
  </div>
</template>

