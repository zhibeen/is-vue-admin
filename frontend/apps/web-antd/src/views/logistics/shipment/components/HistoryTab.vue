<script setup lang="ts">
/**
 * 发货单详情 - 操作日志Tab
 */
import { Card, Timeline, TimelineItem, Input } from 'ant-design-vue';
import { HistoryOutlined } from '@ant-design/icons-vue';
import type { Shipment } from '#/api/logistics/shipment';

interface Props {
  shipment: Shipment | null;
  isEditing: boolean;
  editForm: any;
}

const props = defineProps<Props>();

// 来源文本
const sourceTextMap: Record<string, string> = {
  manual: '手工录入',
  excel: 'Excel导入',
  lingxing: '领星同步',
  yicang: '易仓同步',
};
</script>

<template>
  <div>
    <Card title="备注信息" size="small" class="mb-4">
      <Input.TextArea
        v-if="isEditing"
        v-model:value="editForm.notes"
        placeholder="请输入备注信息"
        :rows="5"
      />
      <div v-else class="p-4 bg-gray-50 dark:bg-gray-900 rounded min-h-[100px] text-gray-600 dark:text-gray-400 leading-relaxed">
        {{ shipment?.notes || '暂无备注' }}
      </div>
    </Card>
    
    <Card title="操作记录" size="small">
      <Timeline>
        <TimelineItem color="green">
          <p class="font-semibold text-sm mb-1">创建发货单</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ shipment?.created_at }}</p>
          <p class="text-xs mt-1 text-gray-500 dark:text-gray-400">来源: {{ sourceTextMap[shipment?.source || ''] }}</p>
        </TimelineItem>
        <TimelineItem v-if="shipment?.status !== 'draft'" color="blue">
          <p class="font-semibold text-sm mb-1">确认发货单</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">状态变更为：已确认</p>
        </TimelineItem>
        <TimelineItem v-if="shipment?.actual_ship_date" color="green">
          <p class="font-semibold text-sm mb-1">实际发货</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ shipment?.actual_ship_date }}</p>
        </TimelineItem>
      </Timeline>
    </Card>
  </div>
</template>

