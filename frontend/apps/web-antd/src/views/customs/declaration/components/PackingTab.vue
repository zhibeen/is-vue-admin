<script setup lang="ts">
import { Descriptions, Table, Input, InputNumber, DatePicker } from 'ant-design-vue';
import { type TaxCustomsDeclaration } from '#/api/customs/declaration';
import { getUnitName } from '../declaration.config';

defineProps<{
  detail: TaxCustomsDeclaration;
  infoConfig: any[];
  columns: any[];
  isEditMode?: boolean; // 新增编辑模式标识
}>();
</script>

<template>
  <div class="p-4">
    <!-- 表头信息区 - 支持编辑 -->
    <Descriptions bordered size="small" :column="4" class="mb-6 custom-descriptions">
      <Descriptions.Item v-for="(item, index) in infoConfig" :key="index" :label="item.label" :span="item.span">
        <!-- 日期字段 - 可编辑 -->
        <DatePicker 
          v-if="isEditMode && item.label.includes('Date')"
          v-model:value="detail.export_date"
          size="small"
          class="w-full"
          value-format="YYYY-MM-DD"
        />
        <!-- 合同号 - 可编辑 -->
        <Input 
          v-else-if="isEditMode && item.label.includes('Contract')"
          v-model:value="detail.contract_no"
          size="small"
          placeholder="请输入合同号"
        />
        <!-- 装运港口 - 可编辑 -->
        <Input 
          v-else-if="isEditMode && item.label.includes('From')"
          v-model:value="detail.loading_port"
          size="small"
          placeholder="请输入装运港"
        />
        <!-- 船名航次 - 可编辑 -->
        <Input 
          v-else-if="isEditMode && item.label.includes('Shipped')"
          v-model:value="detail.conveyance_ref"
          size="small"
          placeholder="请输入船名航次"
        />
        <!-- 只读显示 -->
        <div v-else class="px-1 min-h-[22px] flex items-center">
          {{ item.value }}
        </div>
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
      :scroll="{ x: 1200 }" 
    >
      <template #bodyCell="{ column, record }">
        <!-- 净重 -->
        <template v-if="column.dataIndex === 'net_weight'">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="record.net_weight" 
            size="small" 
            :min="0"
            :precision="4"
            class="w-full"
          />
          <span v-else>{{ record.net_weight }}</span>
        </template>

        <!-- 毛重 -->
        <template v-if="column.dataIndex === 'gross_weight'">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="record.gross_weight" 
            size="small" 
            :min="0"
            :precision="4"
            class="w-full"
          />
          <span v-else>{{ record.gross_weight }}</span>
        </template>

        <!-- 商品名称 -->
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

        <!-- 数量及单位 -->
        <template v-if="column.dataIndex === 'qty_unit'">
          <span v-if="!isEditMode">
            {{ record.qty }}{{ getUnitName(record.unit) }}
          </span>
        </template>
      </template>
    </Table>
    
    <!-- 总计行 - 支持编辑 -->
    <div class="mt-4 flex justify-between px-4 text-sm font-bold text-foreground">
      <div>总计</div>
      <div class="flex gap-8 items-center">
        <div class="flex items-center gap-2">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="detail.pack_count" 
            size="small" 
            :min="0"
            :precision="0"
            class="w-24"
          />
          <span v-else>{{ detail.pack_count }}</span>
          <span class="text-muted-foreground">箱</span>
        </div>
        <div class="flex items-center gap-2">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="detail.net_weight" 
            size="small" 
            :min="0"
            :precision="4"
            class="w-32"
          />
          <span v-else>{{ detail.net_weight }}</span>
          <span class="text-muted-foreground">kg</span>
        </div>
        <div class="flex items-center gap-2">
          <InputNumber 
            v-if="isEditMode" 
            v-model:value="detail.gross_weight" 
            size="small" 
            :min="0"
            :precision="4"
            class="w-32"
          />
          <span v-else>{{ detail.gross_weight }}</span>
          <span class="text-muted-foreground">kg</span>
        </div>
      </div>
    </div>
  </div>
</template>

