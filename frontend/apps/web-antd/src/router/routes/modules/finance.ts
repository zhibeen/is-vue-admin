import type { RouteRecordRaw } from 'vue-router';

import { BasicLayout } from '#/layouts';
import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: 'lucide:wallet',
      order: 30,
      title: $t('财务管理'),
    },
    name: 'Finance',
    path: '/finance',
    children: [
      {
        name: 'FinancePayable',
        path: '/finance/payable',
        component: () => import('#/views/finance/payable/index.vue'),
        meta: {
          icon: 'lucide:file-text',
          title: $t('应付账款管理'),
        },
      },
    ],
  },
];

export default routes;

