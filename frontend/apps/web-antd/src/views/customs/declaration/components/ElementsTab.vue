<script setup lang="ts">
import { Table, Input } from 'ant-design-vue';
import { type TaxCustomsDeclaration } from '#/api/customs/declaration';

defineProps<{
  detail: TaxCustomsDeclaration;
  columns: any[];
  isEditMode?: boolean;
}>();
</script>

<template>
  <div class="p-4">
    <!-- 商品申报要素表 - 支持编辑 -->
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

        <!-- 品牌 (使用自定义渲染固定值，不可编辑) -->
        <template v-if="column.dataIndex === 'brand'">
          <span class="text-muted-foreground">-</span>
        </template>

        <!-- 产品长宽厚 (固定值) -->
        <template v-if="column.dataIndex === 'dimensions'">
          <span class="text-muted-foreground">0 x 0 x 0</span>
        </template>

        <!-- 产品重量 (固定值) -->
        <template v-if="column.dataIndex === 'weight_g'">
          <span class="text-muted-foreground">0</span>
        </template>

        <!-- 型号 (固定值) -->
        <template v-if="column.dataIndex === 'model'">
          <span class="text-muted-foreground">-</span>
        </template>

        <!-- 品牌类型 (固定值) -->
        <template v-if="column.dataIndex === 'brand_type'">
          <span class="text-muted-foreground">无品牌</span>
        </template>

        <!-- 出口享惠情况 (固定值) -->
        <template v-if="column.dataIndex === 'benefit'">
          <span class="text-muted-foreground">不享惠</span>
        </template>

        <!-- 其他申报要素 (固定值) -->
        <template v-if="column.dataIndex === 'other_elements'">
          <span class="text-muted-foreground">-</span>
        </template>
      </template>
    </Table>
  </div>
</template>

