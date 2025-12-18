import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';
import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: 'lucide:file-text',
      order: 1000,
      title: 'SERC 业财税',
    },
    name: 'Serc',
    path: '/serc',
    children: [
      {
        name: 'SercSupply',
        path: 'supply',
        meta: {
          title: '供应链交付',
        },
        children: [
          {
            name: 'SercContractList',
            path: 'contracts',
            component: () => import('#/views/serc/supply/index.vue'),
            meta: {
              title: '交付合同管理',
            },
          },
        ],
      },
      {
        name: 'SercFinance',
        path: 'finance',
        meta: {
          title: '资金结算中心',
        },
        children: [
          {
            name: 'SercSettlement',
            path: 'settlement',
            component: () => import('#/views/serc/finance/settlement.vue'),
            meta: {
              title: '采购结算单',
            },
          },
          {
            name: 'SercPool',
            path: 'pool',
            component: () => import('#/views/serc/finance/pool.vue'),
            meta: {
              title: '资金付款池',
            },
          },
        ],
      },
      {
        name: 'SercConfig',
        path: 'config',
        meta: {
          title: '风控配置',
        },
        children: [
          {
            name: 'SercExchangeRate',
            path: 'exchange-rate',
            component: () => import('#/views/serc/config/exchange-rate.vue'),
            meta: {
              title: '换汇成本',
            },
          },
        ],
      },
      {
        name: 'SercFlow',
        path: 'flow',
        component: () => import('#/views/serc/flow.vue'),
        meta: {
          title: '业务流程图',
        },
      },
    ],
  },
];

export default routes;

