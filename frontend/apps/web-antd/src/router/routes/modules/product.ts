import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:package',
      order: 10,
      title: '产品管理', 
    },
    name: 'Product',
    path: '/product',
    children: [
      {
        name: 'ProductCreate',
        path: 'create',
        component: () => import('#/views/product/create.vue'),
        meta: {
          icon: 'lucide:plus-circle',
          title: '创建产品',
        },
      },
      {
        name: 'CategoryManagement',
        path: 'category',
        component: () => import('#/views/product/category/index.vue'),
        meta: {
          icon: 'lucide:folder-tree',
          title: '品名分类管理',
        },
      },
      {
        name: 'AttributeManagement',
        path: 'attribute',
        component: () => import('#/views/product/attribute/index.vue'),
        meta: {
          icon: 'lucide:list',
          title: '商品属性管理',
        },
      },
      {
        name: 'VehicleManagement',
        path: 'vehicle-aux',
        component: () => import('#/views/product/vehicle-aux/index.vue'),
        meta: {
          icon: 'lucide:car',
          title: '车型辅助目录',
        },
      },
      {
        name: 'HSCodeManagement',
        path: 'hscode',
        component: () => import('#/views/product/hscode/index.vue'),
        meta: {
          icon: 'lucide:book',
          title: 'HS编码库',
        },
      },
      {
        name: 'ProductRules',
        path: 'rules',
        component: () => import('#/views/product/rules/index.vue'),
        meta: {
          icon: 'lucide:settings',
          title: '业务规则配置',
        },
      },
    ],
  },
];

export default routes;
