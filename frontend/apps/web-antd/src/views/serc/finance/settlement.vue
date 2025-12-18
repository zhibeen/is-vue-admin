<script setup lang="ts">
import { useVbenVxeGrid, type VxeGridProps } from '#/adapter/vxe-table';
import { getSOAList, confirmSOA, approveSOA } from '#/api/serc/finance';
import { onMounted, ref } from 'vue';
import { Tag, Button, Popconfirm, message } from 'ant-design-vue';
import { Page, useVbenDrawer } from '@vben/common-ui';
import SoaDetailDrawer from './SoaDetailDrawer.vue';

const gridOptions: VxeGridProps = {
  columns: [
    { field: 'soa_no', title: '结算单号', minWidth: 180 },
    { field: 'supplier_name', title: '供应商', minWidth: 150 },
    { 
        field: 'total_payable', 
        title: '应付总额', 
        minWidth: 120, 
        formatter: ({ cellValue }) => cellValue ? `￥${Number(cellValue).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}` : '￥0.00',
        align: 'right'
    },
    { 
        field: 'paid_amount', 
        title: '已付金额', 
        minWidth: 120, 
        formatter: ({ cellValue }) => cellValue ? `￥${Number(cellValue).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}` : '￥0.00',
        align: 'right'
    },
    { field: 'status', title: 'SOA状态', width: 100, slots: { default: 'status_default' } },
    { field: 'payment_status', title: '资金状态', width: 100 },
    { field: 'invoice_status', title: '票据状态', width: 100 },
    { field: 'created_at', title: '创建日期', width: 150 },
    { title: '操作', width: 250, fixed: 'right', slots: { default: 'action_default' } },
  ],
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        const res = await getSOAList({
          page: page.currentPage,
          per_page: page.pageSize,
        });
        
        const list = Array.isArray(res) ? res : (res as any).data || [];
        
        return {
          items: list,
          total: list.length, 
        };
      },
    },
  },
  pagerConfig: {
    enabled: true,
  },
  toolbarConfig: {
    custom: true,
    export: true,
    refresh: true,
    resizable: true,
    search: true,
    zoom: true,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

const [DetailDrawer, detailDrawerApi] = useVbenDrawer({
  connectedComponent: SoaDetailDrawer,
});

async function handleConfirm(row: any) {
    try {
        gridApi.setLoading(true);
        await confirmSOA(row.id);
        message.success('SOA 已确认');
        gridApi.reload();
    } catch(e) {
        console.error(e);
    } finally {
        gridApi.setLoading(false);
    }
}

async function handleApprove(row: any) {
    try {
        gridApi.setLoading(true);
        await approveSOA(row.id);
        message.success('SOA 已批准，付款计划已生成');
        gridApi.reload();
    } catch(e) {
        console.error(e);
    } finally {
        gridApi.setLoading(false);
    }
}

function handleView(row: any) {
    detailDrawerApi.setData({ row });
    detailDrawerApi.open();
}

onMounted(() => {
  // gridApi.query(); 
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
        <template #status_default="{ row }">
            <Tag v-if="row.status === 'draft'" color="orange">草稿</Tag>
            <Tag v-else-if="row.status === 'confirmed'" color="blue">已确认</Tag>
            <Tag v-else-if="row.status === 'approved'" color="green">已批准</Tag>
            <Tag v-else>{{ row.status }}</Tag>
        </template>

        <template #action_default="{ row }">
            <Button type="link" size="small" @click="handleView(row)">查看</Button>
            
            <Popconfirm 
                v-if="row.status === 'draft'" 
                title="确定要确认此结算单吗? (意味着供应商已核对无误)" 
                @confirm="handleConfirm(row)"
            >
                <Button type="link" size="small">确认对账</Button>
            </Popconfirm>

            <Popconfirm 
                v-if="row.status === 'confirmed'" 
                title="确定批准此结算单并生成付款计划吗?" 
                @confirm="handleApprove(row)"
            >
                <Button type="link" size="small">批准付款</Button>
            </Popconfirm>
        </template>
    </Grid>
    <DetailDrawer />
  </Page>
</template>
