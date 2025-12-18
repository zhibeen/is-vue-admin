import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    path: '/customs',
    name: 'Customs',
    component: BasicLayout,
    meta: {
      title: '关务管理',
      icon: 'lucide:container',
      order: 30, // Adjust order as needed
    },
    children: [
      {
        path: 'declaration',
        name: 'CustomsDeclaration',
        component: () => import('#/views/customs/declaration/index.vue'),
        meta: {
          title: '报关单管理',
          icon: 'lucide:file-text',
        },
      },
      {
        path: 'products',
        name: 'CustomsProductList',
        component: () => import('#/views/customs/product/index.vue'),
        meta: {
          title: '归类商品库',
          icon: 'lucide:library',
        },
      },
      {
        path: 'consignee',
        name: 'CustomsConsigneeList',
        component: () => import('#/views/customs/consignee/index.vue'),
        meta: {
          title: '境外收货人',
          icon: 'lucide:users',
        },
      },
      {
        path: 'declaration/detail/:id',
        name: 'DeclarationDetail',
        component: () => import('#/views/customs/declaration/DeclarationDetail.vue'),
        meta: {
          title: '报关单详情',
          hideInMenu: true,
          hideMenu: true,
          currentActiveMenu: '/customs/declaration',
        },
      },
    ],
  },
];

export default routes;

