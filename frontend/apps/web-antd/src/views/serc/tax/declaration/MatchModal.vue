<script setup lang="ts">
import { ref } from 'vue';
import { useVbenModal } from '@vben/common-ui';
import { matchDeclaration, confirmMatch, type MatchResponse } from '#/api/serc/tax';
import { message, Table, Tag, Button } from 'ant-design-vue';

const loading = ref(false);
const confirming = ref(false);
const matchResult = ref<MatchResponse | null>(null);
const currentId = ref<number | null>(null);

const [ModalComponent, modalApi] = useVbenModal({
  title: '报关单发票智能匹配',
  size: 'large',
  onOpenChange: async (isOpen) => {
    if (isOpen) {
      const { id } = modalApi.getData();
      currentId.value = id;
      await runMatch(id);
    } else {
      matchResult.value = null;
      currentId.value = null;
    }
  },
});

async function runMatch(id: number) {
  try {
    loading.value = true;
    modalApi.setState({ loading: true });
    matchResult.value = await matchDeclaration(id);
  } catch (e) {
    message.error('匹配计算失败');
  } finally {
    loading.value = false;
    modalApi.setState({ loading: false });
  }
}

async function handleConfirm() {
  if (!currentId.value || !matchResult.value?.success) return;
  
  try {
    confirming.value = true;
    await confirmMatch(currentId.value);
    message.success('匹配成功，发票已锁定');
    modalApi.close();
    // emit success to refresh parent list?
  } catch (e) {
    message.error('确认匹配失败');
  } finally {
    confirming.value = false;
  }
}

const columns = [
  { title: '报关项ID', dataIndex: 'item_id', width: 80 },
  { title: '品名', dataIndex: 'product_name', width: 150 },
  { title: '状态', dataIndex: 'status', width: 100 },
  { title: '失败原因', dataIndex: 'reason', width: 200 },
];

const innerColumns = [
  { title: '发票号', dataIndex: 'invoice_no' },
  { title: '占用数量', dataIndex: 'take_qty' },
];
</script>

<template>
  <ModalComponent>
    <div v-if="loading" class="p-4 text-center">正在计算最佳凑数方案...</div>
    <div v-else-if="matchResult">
      <div class="mb-4 flex justify-between items-center">
        <Tag :color="matchResult.success ? 'green' : 'red'">
          {{ matchResult.success ? '全单匹配成功' : '存在未匹配项' }}
        </Tag>
        <Button 
          type="primary" 
          :disabled="!matchResult.success" 
          :loading="confirming"
          @click="handleConfirm"
        >
          确认锁定发票
        </Button>
      </div>

      <Table 
        :dataSource="matchResult.results" 
        :columns="columns"
        size="small"
        :pagination="false"
        rowKey="item_id"
      >
        <template #expandedRowRender="{ record }">
          <Table 
             v-if="record.plan && record.plan.length"
             :dataSource="record.plan"
             :columns="innerColumns"
             size="small"
             :pagination="false"
             :showHeader="true"
          />
          <div v-else class="text-gray-400 pl-4 py-2">无匹配发票</div>
        </template>
        
        <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'">
                 <Tag :color="record.status === 'success' ? 'green' : 'red'">
                    {{ record.status === 'success' ? '成功' : '失败' }}
                 </Tag>
            </template>
        </template>
      </Table>
    </div>
  </ModalComponent>
</template>
