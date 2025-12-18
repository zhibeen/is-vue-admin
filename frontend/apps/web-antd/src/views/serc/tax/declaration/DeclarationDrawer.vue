<script setup lang="ts">
import { ref, watch } from 'vue';
import { useVbenDrawer } from '@vben/common-ui';
import { Input, DatePicker, InputNumber, Alert, Form, message } from 'ant-design-vue';
import { checkRisk, createDeclaration, type RiskCheckResponse } from '#/api/serc/tax';
import { useDebounceFn } from '@vueuse/core';
import dayjs from 'dayjs';

const formState = ref({
    entry_no: '',
    export_date: undefined,
    destination_country: 'USA', // Default
    fob_total: 0,
    cost_total: 0, // Auxiliary field for risk check
    exchange_rate: 7.0,
    items: []
});

const riskResult = ref<RiskCheckResponse | null>(null);
const riskLoading = ref(false);
const submitting = ref(false);

const [DrawerComponent, drawerApi] = useVbenDrawer({
    title: '报关单填报 (含实时风控)',
    size: 'large',
    onConfirm: handleSubmit
});

// Real-time risk check
const debouncedCheckRisk = useDebounceFn(async () => {
    if (!formState.value.fob_total || !formState.value.cost_total) return;
    
    try {
        riskLoading.value = true;
        const res = await checkRisk({
            fob_amount: formState.value.fob_total,
            cost_amount: formState.value.cost_total,
            currency: 'USD'
        });
        riskResult.value = res;
    } finally {
        riskLoading.value = false;
    }
}, 500);

watch(
    () => [formState.value.fob_total, formState.value.cost_total], 
    () => {
        riskResult.value = null;
        debouncedCheckRisk();
    }
);

async function handleSubmit() {
    if (riskResult.value?.is_blocked) {
        message.error('风控未通过，无法提交');
        return;
    }
    
    try {
        submitting.value = true;
        drawerApi.setState({ loading: true });
        
        await createDeclaration({
            entry_no: formState.value.entry_no,
            destination_country: formState.value.destination_country,
            fob_total: formState.value.fob_total,
            exchange_rate: formState.value.exchange_rate,
            export_date: formState.value.export_date ? dayjs(formState.value.export_date).format('YYYY-MM-DD') : undefined,
            items: [] // In real app, we need item details
        });
        
        message.success('报关单创建成功');
        drawerApi.close();
        // emit success?
    } catch (e) {
        console.error(e);
        // message handled by global interceptor?
    } finally {
        submitting.value = false;
        drawerApi.setState({ loading: false });
    }
}
</script>

<template>
    <DrawerComponent>
        <Form layout="vertical">
             <!-- Basic Fields -->
             <div class="grid grid-cols-2 gap-4">
                 <Form.Item label="报关单号">
                     <Input v-model:value="formState.entry_no" />
                 </Form.Item>
                 <Form.Item label="出口日期">
                     <DatePicker v-model:value="formState.export_date" style="width: 100%" />
                 </Form.Item>
                 <Form.Item label="FOB总额 (USD)">
                     <InputNumber v-model:value="formState.fob_total" style="width: 100%" :min="0" />
                 </Form.Item>
                  <Form.Item label="采购成本 (CNY) [仅风控用]">
                     <InputNumber v-model:value="formState.cost_total" style="width: 100%" :min="0" />
                 </Form.Item>
             </div>

             <!-- Risk Alert -->
             <div v-if="riskResult" class="mb-4">
                 <Alert
                     v-if="riskResult.is_blocked"
                     type="error"
                     show-icon
                     message="风控阻断"
                     :description="riskResult.reason"
                 />
                 <Alert
                     v-else-if="riskResult.reason"
                     type="warning"
                     show-icon
                     message="风控预警"
                     :description="riskResult.reason"
                 />
                 <Alert
                     v-else
                     type="success"
                     show-icon
                     message="风控通过"
                     :description="`当前换汇成本: ${riskResult.cost.toFixed(2)}`"
                 />
             </div>
        </Form>
    </DrawerComponent>
</template>
