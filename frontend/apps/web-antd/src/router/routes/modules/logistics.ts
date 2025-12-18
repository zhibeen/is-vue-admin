import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    path: '/logistics',
    name: 'Logistics',
    component: BasicLayout,
    meta: {
      title: '物流管理',
      icon: 'lucide:truck',
      order: 25, // 在关务管理(30)之前
    },
    children: [
      {
        path: 'shipment',
        name: 'ShipmentOrderList',
        component: () => import('#/views/logistics/shipment/index.vue'),
        meta: {
          title: '发货单管理',
          icon: 'lucide:package',
        },
      },
    ],
  },
];

export default routes;

