import { requestClient } from '#/api/request';
import type { Stock, StockMovement } from './model';

enum Api {
  Stock = '/v1/stocks',
}

/**
 * 获取库存列表
 */
export function getStockList(params?: any) {
  return requestClient.get<{ items: Stock[]; total: number }>(Api.Stock, {
    params,
  });
}

/**
 * 获取库存详情
 */
export function getStock(sku: string, warehouseId: number) {
  return requestClient.get<Stock>(`${Api.Stock}/${sku}/warehouses/${warehouseId}`);
}

/**
 * 库存调整
 */
export function adjustStock(data: {
  sku: string;
  warehouse_id: number;
  quantity: number;
  type: 'in' | 'out' | 'adjust' | 'transfer';
  reason?: string;
  target_warehouse_id?: number; // for transfer
}) {
  return requestClient.post<Stock>(`${Api.Stock}/adjust`, data);
}

/**
 * 获取库存流水
 */
export function getStockMovements(params?: any) {
  return requestClient.get<{ items: StockMovement[]; total: number }>(
    `${Api.Stock}/movements`, 
    { params }
  );
}

/**
 * 获取库存汇总
 */
export function getStockSummary() {
  return requestClient.get<any>(`${Api.Stock}/summary`);
}

