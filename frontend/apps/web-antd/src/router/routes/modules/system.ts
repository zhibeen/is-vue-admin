import type { RouteRecordRaw } from 'vue-router';

import { BasicLayout } from '#/layouts';
import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: 'lucide:settings',
      order: 2000,
      title: '系统管理',
    },
    name: 'System',
    path: '/system',
    children: [
      {
        name: 'UserManagement',
        path: 'user',
        component: () => import('#/views/system/user/index.vue'),
        meta: {
          title: '用户管理',
        },
      },
      {
        name: 'RoleManagement',
        path: 'role',
        component: () => import('#/views/system/role/index.vue'),
        meta: {
          title: '角色管理',
        },
      },
      {
        name: 'CompanyManagement',
        path: 'company',
        component: () => import('#/views/system/company/index.vue'),
        meta: {
          title: '采购主体',
        },
      },
      {
        name: 'DictManagement',
        path: 'dict',
        component: () => import('#/views/system/dict/index.vue'),
        meta: {
          title: '字典管理',
        },
      },
    ],
  },
];

export default routes;

