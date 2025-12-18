<script setup lang="ts">
import { Descriptions, Table, Input, InputNumber } from 'ant-design-vue';
import { type TaxCustomsDeclaration } from '#/api/customs/declaration';

defineProps<{
  detail: TaxCustomsDeclaration;
  infoConfig: any[];
  columns: any[];
  isEditMode?: boolean;
}>();
</script>

<template>
  <div class="p-4">
    <!-- 表头信息区 - 支持编辑 -->
    <Descriptions bordered size="small" :column="4" class="mb-6 custom-descriptions">
      <Descriptions.Item v-for="(item, index) in infoConfig" :key="index" :label="item.label" :span="item.span">
        <!-- 提运单号 - 可编辑 -->
        <div v-if="item.label.includes('提运单号')">
          <Input 
            v-if="isEditMode"
            v-model:value="detail.bill_of_lading_no"
            size="small"
            placeholder="提运单号"
          />
          <span v-else>{{ item.value }}</span>
        </div>
        
        <!-- 净重 - 可编辑 -->
        <div v-else-if="item.label.includes('净重')">
          <div v-if="isEditMode" class="flex items-center gap-1">
            <InputNumber 
              v-model:value="detail.net_weight"
              size="small"
              :min="0"
              :precision="4"
              class="flex-1"
            />
            <span class="text-muted-foreground text-xs">kg</span>
          </div>
          <span v-else>{{ item.value }}</span>
        </div>
        
        <!-- 毛重 - 可编辑 -->
        <div v-else-if="item.label.includes('毛重')">
          <div v-if="isEditMode" class="flex items-center gap-1">
            <InputNumber 
              v-model:value="detail.gross_weight"
              size="small"
              :min="0"
              :precision="4"
              class="flex-1"
            />
            <span class="text-muted-foreground text-xs">kg</span>
          </div>
          <span v-else>{{ item.value }}</span>
        </div>
        
        <!-- 其他字段只读显示 -->
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
    >
      <template #bodyCell="{ column, record }">
        <!-- 品名 -->
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

        <!-- 海关HS编码 -->
        <template v-if="column.dataIndex === 'hs_code'">
          <Input 
            v-if="isEditMode" 
            v-model:value="record.hs_code" 
            size="small" 
          />
          <span v-else>{{ record.hs_code }}</span>
        </template>
      </template>
    </Table>
  </div>
</template>

