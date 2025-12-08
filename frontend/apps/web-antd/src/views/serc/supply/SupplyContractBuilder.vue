<script setup lang="ts">
import { ref, computed } from 'vue';
import { useVbenDrawer } from '@vben/common-ui';
import { Drawer, Button, message, Table, Descriptions, Alert, Tag, InputNumber, Input } from 'ant-design-vue';
import { previewSupplyContract, generateSupplyContract } from '#/api/serc/finance_supply';
import type { SupplyContractPreview, SupplyContractItem } from '#/api/serc/finance_supply';

const loading = ref(false);
const previewData = ref<SupplyContractPreview | null>(null);
const l1Contract = ref<any>(null);

const [DrawerComponent, drawerApi] = useVbenDrawer({
  title: '编制结算书 (L1.5 供货合同)',
  size: 'large',
  onOpenChange: async (isOpen) => {
    if (isOpen) {
      const { l1Contract: contract } = drawerApi.getData();
      l1Contract.value = contract;
      await loadPreview(contract.id);
    } else {
        previewData.value = null;
    }
  },
});

async function loadPreview(l1Id: number) {
  try {
    loading.value = true;
    drawerApi.setState({ loading: true });
    const res = await previewSupplyContract(l1Id);
    
    // Add unique key for table
    if (res.items) {
        res.items = res.items.map((item, index) => ({...item, key: index}));
    }
    previewData.value = res;
  } catch (e) {
    message.error('无法加载预览数据');
    console.error(e);
  } finally {
    loading.value = false;
    drawerApi.setState({ loading: false });
  }
}

async function handleConfirm() {
    if (!previewData.value) return;
    
    // Final balance check
    if (Math.abs(previewData.value.diff) > 0.05) {
        message.error('金额差异过大，无法生成合同');
        return;
    }

    try {
        loading.value = true;
        await generateSupplyContract({
            l1_contract_id: l1Contract.value.id,
            confirmed_items: previewData.value.items
        });
        message.success('供货合同生成成功！');
        drawerApi.close();
        // Emit success? Or just close.
    } catch(e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
}

// --- Table Columns ---
const columns = [
    { title: '开票品名', dataIndex: 'invoice_name', width: 200, customRender: ({record}: any) => {
        // Allow editing? For now just display
        return record.invoice_name; 
    }},
    { title: '单位', dataIndex: 'invoice_unit', width: 80 },
    { title: '数量', dataIndex: 'quantity', width: 100 },
    { title: '含税单价', dataIndex: 'price_unit', width: 120, customRender: ({text}: any) => Number(text).toFixed(4) },
    { title: '行总价', dataIndex: 'amount', width: 120, customRender: ({text}: any) => Number(text).toFixed(2) },
    { title: '税率', dataIndex: 'tax_rate', width: 100, customRender: ({text}: any) => `${(Number(text)*100).toFixed(0)}%` },
    { title: '税收编码', dataIndex: 'tax_code', width: 150 },
];

</script>

<template>
  <DrawerComponent>
    <div v-if="loading" class="p-8 text-center">
        加载中...
    </div>
    <div v-else-if="previewData" class="p-4 space-y-6">
        
        <!-- Header Info -->
        <Descriptions title="L1 交付单信息" bordered size="small">
            <Descriptions.Item label="交付单号">{{ previewData.contract_no }}</Descriptions.Item>
            <Descriptions.Item label="供应商">{{ previewData.supplier_name }}</Descriptions.Item>
            <Descriptions.Item label="交付总额">
                <span class="font-bold">￥{{ Number(previewData.l1_total_amount).toLocaleString() }}</span>
            </Descriptions.Item>
        </Descriptions>

        <!-- Warnings -->
        <Alert 
            v-if="previewData.warnings && previewData.warnings.length" 
            type="warning" 
            show-icon
            class="mb-4"
        >
            <template #message>
                <div v-for="(warn, idx) in previewData.warnings" :key="idx">
                    {{ warn }}
                </div>
            </template>
        </Alert>

        <!-- Preview Table -->
        <div>
            <div class="flex justify-between items-center mb-2">
                <h3 class="font-bold text-lg">L1.5 票据明细 (预览)</h3>
                <Tag color="blue">自动聚合</Tag>
            </div>
            
            <Table 
                :dataSource="previewData.items" 
                :columns="columns" 
                size="small" 
                :pagination="false"
                bordered
            />
        </div>

        <!-- Summary Footer -->
        <div class="bg-gray-50 p-4 rounded border flex justify-between items-center">
            <div class="space-x-4">
                <span>票据总额: <span class="font-bold text-lg">￥{{ Number(previewData.preview_total_amount).toLocaleString() }}</span></span>
                
                <span :class="{'text-green-600': previewData.is_balanced, 'text-red-600': !previewData.is_balanced}">
                    差额: {{ Number(previewData.diff).toFixed(2) }}
                </span>
            </div>
            <Button type="primary" size="large" :disabled="!previewData.is_balanced" @click="handleConfirm">
                确认生成结算书
            </Button>
        </div>

    </div>
  </DrawerComponent>
</template>

