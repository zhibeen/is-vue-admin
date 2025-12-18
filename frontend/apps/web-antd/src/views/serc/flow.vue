<script setup lang="ts">
import { onMounted, ref } from 'vue';
import mermaid from 'mermaid';

const diagram = `
graph TD
    %% --- 角色定义 ---
    subgraph SCM [供应链 & 交付]
        L1[L1 交付合同]
    end

    subgraph FIN [财务 & 资金]
        L1_5["L1.5 供货合同<br/>(票据聚合/税率调整)"]
        L2_Draft["L2 结算单 (SOA)<br/>状态: 草稿"]
        L2_Confirmed["L2 结算单<br/>状态: 供应商已确认"]
        L2_Approved["L2 结算单<br/>状态: 已批准"]
        Pool["L3 资金池<br/>(待付项)"]
        Pay[L3 付款申请单]
        Invoice[进项发票]
    end

    subgraph TAX [关务 & 风控]
        Dec_Draft["报关单填报<br/>(草稿)"]
        Risk{换汇成本风控}
        Match_Algo{智能凑数算法}
        Dec_Pre["报关单<br/>(预申报)"]
        Refund[退税申报]
    end

    %% --- 流程连线 ---
    
    %% 1. 财务结算流
    L1 -->|1. 生成| L1_5
    L1_5 -->|2. 合并生成| L2_Draft
    L2_Draft -->|3. 线下对账| L2_Confirmed
    L2_Confirmed -->|4. 批准| L2_Approved
    L2_Approved -->|5. 入池| Pool
    Pool -->|6. 合并支付| Pay
    
    %% 发票回流
    L2_Confirmed -.->|供应商开票| Invoice
    
    %% 2. 税务风控流
    Dec_Draft -->|实时检查| Risk
    Risk -->|阻断| Dec_Draft
    Risk -->|通过| Match_Algo
    
    %% 匹配逻辑
    Invoice -->|提供额度| Match_Algo
    Match_Algo -->|匹配成功| Dec_Pre
    
    %% 状态锁定
    Dec_Pre -.->|锁定| Invoice
    
    %% 逆向流程
    Dec_Pre -->|解除匹配| Dec_Draft
    Dec_Pre -->|正式申报| Refund
`;

const container = ref<HTMLElement | null>(null);

onMounted(async () => {
  mermaid.initialize({ startOnLoad: false, theme: 'default' });
  if (container.value) {
    const { svg } = await mermaid.render('mermaid-svg', diagram);
    container.value.innerHTML = svg;
  }
});
</script>

<template>
  <div class="p-4 bg-white min-h-screen">
    <div class="mb-4">
      <h2 class="text-xl font-bold">SERC 核心业务流程图</h2>
      <p class="text-gray-500">展示从供应链交付到财务结算、再到税务退税的完整闭环。</p>
    </div>
    <div ref="container" class="mermaid-container border rounded p-4 flex justify-center"></div>
  </div>
</template>

<style scoped>
.mermaid-container {
  overflow-x: auto;
}
</style>

