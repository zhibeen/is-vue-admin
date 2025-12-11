import { requestClient } from '#/api/request';
import type { StockDiscrepancy, ThirdPartyWarehouse } from './model';

enum Api {
  Sync = '/v1/sync',
}

/**
 * 同步指定仓库库存
 */
export function syncWarehouseStock(warehouseId: number) {
  return requestClient.post<{ data: any }>(`${Api.Sync}/warehouses/${warehouseId}`);
}

/**
 * 同步所有仓库库存
 */
export function syncAllStock() {
  return requestClient.post<{ task_id: string }>(`${Api.Sync}/all`);
}

/**
 * 获取库存差异列表
 */
export function getStockDiscrepancies(params?: any) {
  return requestClient.get<{ items: StockDiscrepancy[]; total: number }>(
    `${Api.Sync}/discrepancies`, 
    { params }
  );
}

/**
 * 解决库存差异
 */
export function resolveStockDiscrepancy(
  discrepancyId: number, 
  data: { 
    action: 'sync_to_system' | 'sync_to_platform' | 'ignore'; 
    note?: string 
  }
) {
  return requestClient.post<StockDiscrepancy>(
    `${Api.Sync}/discrepancies/${discrepancyId}/resolve`, 
    data
  );
}

/**
 * 获取第三方仓库列表
 */
export function getThirdPartyWarehouses() {
  return requestClient.get<{ items: ThirdPartyWarehouse[] }>(
    `${Api.Sync}/third-party-warehouses`
  );
}

