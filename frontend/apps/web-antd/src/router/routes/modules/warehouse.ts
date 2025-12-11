import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    path: '/wms',
    name: 'WMS',
    component: BasicLayout,
    meta: {
      title: '仓库系统',
      icon: 'lucide:warehouse',
      order: 10,
    },
    children: [
      // --- 库存板块 ---
      {
        path: 'stock',
        name: 'WmsStock',
        meta: { title: '库存管理' },
        children: [
          {
            path: 'current',
            name: 'StockCurrent',
            component: () => import('#/views/stock/overview/index.vue'),
            meta: { title: '仓库即时库存' },
          },
          {
            path: 'detail',
            name: 'StockDetail',
            component: () => import('#/views/stock/overview/index.vue'), // 暂时复用，通过 props 区分
            meta: { title: '库存明细' },
          },
          {
            path: 'fba',
            name: 'StockFba',
            component: () => import('#/views/common/placeholder.vue'), // 占位
            meta: { title: 'FBA库存明细' },
          },
        ],
      },
      
      // --- 虚拟仓管理板块 ---
      {
        path: 'virtual',
        name: 'WmsVirtual',
        meta: { title: '虚拟仓管理' },
        children: [
          {
            path: 'list',
            name: 'VirtualList',
            component: () => import('#/views/virtual/list/index.vue'),
            meta: { title: '虚拟仓列表' },
          },
          {
            path: 'detail/:id',
            name: 'VirtualDetail',
            component: () => import('#/views/virtual/detail/index.vue'),
            meta: {
              title: '虚拟仓详情',
              hideInMenu: true,
            },
          },
          {
            path: 'product-group',
            name: 'VirtualProductGroup',
            component: () => import('#/views/virtual/product-group/index.vue'),
            meta: { title: 'SKU分组管理' },
          },
          {
            path: 'stock-calc',
            name: 'VirtualStockCalc',
            component: () => import('#/views/virtual/stock/index.vue'),
            meta: { title: '库存计算' },
          },
        ],
      },
      
      // --- 收货板块 ---
      {
        path: 'receiving',
        name: 'WmsReceiving',
        meta: { title: '收货管理' },
        children: [
          {
            path: 'list',
            name: 'ReceivingList',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '收货单' },
          },
          {
            path: 'return',
            name: 'SalesReturn',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '销售退货单' },
          },
          {
            path: 'qc',
            name: 'QualityControl',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '质检单' },
          },
        ],
      },

      // --- 海外仓板块 ---
      {
        path: 'overseas',
        name: 'WmsOverseas',
        meta: { title: '海外仓管理' },
        children: [
          {
            path: 'plan',
            name: 'OverseasPlan',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '发货计划', affix: true }, // 标星
          },
          {
            path: 'replenishment',
            name: 'OverseasReplenishment',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '海外仓备货单' },
          },
        ],
      },

      // --- 出入库板块 ---
      {
        path: 'operation',
        name: 'WmsOperation',
        meta: { title: '出入库作业' },
        children: [
          {
            path: 'inbound',
            name: 'OperationInbound',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '入库单' },
          },
          {
            path: 'outbound',
            name: 'OperationOutbound',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '出库单' },
          },
          {
            path: 'transfer',
            name: 'OperationTransfer',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '调拨单' },
          },
          {
            path: 'adjust',
            name: 'OperationAdjust',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '调整单' },
          },
          {
            path: 'count',
            name: 'OperationCount',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '盘点单' },
          },
          {
            path: 'movement',
            name: 'OperationMovement',
            component: () => import('#/views/stock/movement/index.vue'),
            meta: { title: '库存流水' },
          },
        ],
      },

      // --- 发货板块 ---
      {
        path: 'shipping',
        name: 'WmsShipping',
        meta: { title: '发货管理' },
        children: [
          {
            path: 'order',
            name: 'ShippingOrder',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '物流下单' },
          },
          {
            path: 'wave',
            name: 'WaveManagement',
            component: () => import('#/views/common/placeholder.vue'),
            meta: { title: '波次管理' },
          },
        ],
      },

      // --- 基础设置 (隐藏在最后或单独板块) ---
      {
        path: 'settings',
        name: 'WmsSettings',
        meta: { title: '仓库设置' },
        children: [
          {
            path: 'warehouse',
            name: 'WarehouseList',
            component: () => import('#/views/warehouse/list/index.vue'),
            meta: { title: '仓库列表' },
          },
          {
            path: 'third-party',
            name: 'ThirdPartyServiceList',
            component: () => import('#/views/warehouse/third-party/index.vue'),
            meta: { title: '三方服务管理' },
          },
          {
            path: 'third-party/detail/:id',
            name: 'ThirdPartyServiceDetail',
            component: () => import('#/views/warehouse/third-party/detail/index.vue'),
            meta: { 
              title: '三方服务详情',
              hideInMenu: true,
              activeMenu: '/wms/settings/third-party'
            },
          },
          {
            path: 'warehouse/detail/:id',
            name: 'WarehouseDetail',
            component: () => import('#/views/warehouse/detail/index.vue'),
            meta: {
              title: '仓库详情',
              hideInMenu: true,
            },
          },
        ],
      },
    ],
  },
];

export default routes;
