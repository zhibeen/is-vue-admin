import type { RouteRecordRaw } from 'vue-router';

import { BasicLayout } from '#/layouts';
import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: 'lucide:truck',
      order: 25,
      title: $t('物流管理'),
    },
    name: 'Logistics',
    path: '/logistics',
    children: [
      {
        name: 'LogisticsShipmentList',
        path: '/logistics/shipment',
        component: () => import('#/views/logistics/shipment/index.vue'),
        meta: {
          icon: 'lucide:package',
          title: $t('发货单管理'),
        },
      },
      {
        name: 'LogisticsShipmentDetail',
        path: '/logistics/shipment/:id',
        component: () => import('#/views/logistics/shipment/detail.vue'),
        meta: {
          hideInMenu: true,
          title: $t('发货单详情'),
          activePath: '/logistics/shipment',
        },
      },
      {
        name: 'LogisticsProvider',
        path: '/logistics/provider',
        component: () => import('#/views/logistics/provider/index.vue'),
        meta: {
          icon: 'lucide:building-2',
          title: $t('物流服务商管理'),
        },
      },
      {
        name: 'LogisticsStatement',
        path: '/logistics/statement',
        component: () => import('#/views/logistics/statement/index.vue'),
        meta: {
          icon: 'lucide:file-text',
          title: $t('物流对账管理'),
        },
      },
      {
        name: 'LogisticsStatementDetail',
        path: '/logistics/statement/:id',
        component: () => import('#/views/logistics/statement/detail.vue'),
        meta: {
          hideInMenu: true,
          title: $t('对账单详情'),
          activePath: '/logistics/statement',
        },
      },
    ],
  },
];

export default routes;
