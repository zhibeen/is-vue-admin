import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';
import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: 'lucide:shopping-cart',
      order: 20, // Adjust order as needed
      title: '采购管理',
    },
    name: 'Purchase',
    path: '/purchase',
    children: [
      {
        name: 'PurchaseSupplierManagement',
        path: 'supplier',
        component: () => import('#/views/purchase/supplier/index.vue'),
        meta: {
          icon: 'lucide:users',
          title: '供应商管理',
        },
      },
    ],
  },
];

export default routes;

