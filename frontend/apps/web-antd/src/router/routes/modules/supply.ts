import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    path: '/supply',
    name: 'Supply',
    component: BasicLayout,
    meta: {
      title: '供应链管理',
      icon: 'lucide:link',
      order: 40,
    },
    children: [
      {
        path: 'delivery-contracts',
        name: 'DeliveryContractList',
        component: () => import('#/views/supply/delivery-contract/index.vue'),
        meta: {
          title: '交付合同',
          icon: 'lucide:file-signature',
        },
      },
      {
        path: 'supply-contracts',
        name: 'SupplyContractList',
        component: () => import('#/views/supply/supply-contract/index.vue'),
        meta: {
          title: '开票合同',
          icon: 'lucide:receipt',
        },
      },
    ],
  },
];

export default routes;

