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
        name: 'ProductSPU',
        path: 'spu',
        meta: {
          icon: 'lucide:shopping-bag',
          title: '产品列表 (SPU)',
        },
        children: [
           {
             name: 'ProductSPUList',
             path: '', // /product/spu
             component: () => import('#/views/product/spu/index.vue'),
             meta: {
                title: '产品列表',
                hideInMenu: true,
             }
           },
           {
             name: 'ProductSPUCreate',
             path: 'create', // /product/spu/create
             component: () => import('#/views/product/spu/create.vue'),
             meta: {
                title: '新建产品',
                hideInMenu: true, 
                currentActiveMenu: '/product/spu',
             }
           },
           {
             name: 'ProductSPUEdit',
             path: 'edit/:id', // /product/spu/edit/123
             component: () => import('#/views/product/spu/create.vue'), // Reuse create view
             meta: {
                title: '编辑产品',
                hideInMenu: true,
                currentActiveMenu: '/product/spu',
             }
           },
           {
             name: 'ProductSPUDetail',
             path: 'detail/:id', // /product/spu/detail/123
             component: () => import('#/views/product/spu/create.vue'), // Reuse create view
             meta: {
                title: '产品详情',
                hideInMenu: true,
                currentActiveMenu: '/product/spu',
             }
           }
        ]
      },
      // 新增: SKU管理路由
      {
        name: 'ProductSKU',
        path: 'sku',
        meta: {
          icon: 'lucide:barcode',
          title: 'SKU管理',
        },
        children: [
          {
            name: 'ProductSKUList',
            path: '', // /product/sku
            component: () => import('#/views/product/sku/index.vue'),
            meta: {
              title: 'SKU列表',
              hideInMenu: true,
            }
          },
          {
            name: 'ProductSKUDetail',
            path: 'detail/:sku', // /product/sku/detail/101120501DWD
            component: () => import('#/views/product/sku/detail.vue'),
            meta: {
              title: 'SKU详情',
              hideInMenu: true,
              currentActiveMenu: '/product/sku',
            }
          }
        ]
      },
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
