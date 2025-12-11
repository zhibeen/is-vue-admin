import { requestClient } from '#/api/request';

/**
 * 库存余额模型
 */
export interface Stock {
  id: number;
  sku: string;
  warehouse_id: number;
  physical_quantity: number;
  available_quantity: number;
  allocated_quantity: number;
  in_transit_quantity: number;
  damaged_quantity: number;
  batch_no?: string;
  weight?: number;
  volume?: number;
  updated_at: string;
}

/**
 * 库存流水模型
 */
export interface StockMovement {
  id: number;
  sku: string;
  warehouse_id: number;
  location_id?: number;
  order_type: 'inbound' | 'outbound' | 'transfer' | 'adjustment';
  order_no: string;
  biz_time: string;
  quantity_delta: number;
  batch_no?: string;
  unit_cost?: number;
  currency?: string;
  status: string;
  created_by?: number;
  created_at: string;
}

/**
 * 库存查询参数
 */
export interface StockQuery {
  page?: number;
  per_page?: number;
  sku?: string;
  warehouse_id?: number;
  keyword?: string; // 支持同时搜索SKU或仓库名
}

/**
 * 流水查询参数
 */
export interface StockMovementQuery {
  page?: number;
  per_page?: number;
  sku?: string;
  warehouse_id?: number;
  order_no?: string;
  order_type?: string;
  start_date?: string;
  end_date?: string;
}

/**
 * 获取库存余额列表
 */
export function getStockList(params: StockQuery) {
  return requestClient.get<{ items: Stock[]; total: number }>('/v1/stocks', { params });
}

/**
 * 获取库存流水列表
 */
export function getStockMovementList(params: StockMovementQuery) {
  return requestClient.get<{ items: StockMovement[]; total: number }>('/v1/stocks/movements', { params });
}

