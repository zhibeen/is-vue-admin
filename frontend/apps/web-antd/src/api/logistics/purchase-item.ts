/**
 * 发货单采购明细API接口
 */
import { requestClient } from '#/api/request';

// 采购明细接口
export interface PurchaseItem {
  id?: number;
  shipment_order_id?: number;
  purchase_order_id?: number;
  purchase_order_no?: string;
  purchase_line_id?: number;
  product_variant_id: number;
  sku: string;
  product_name: string;
  quantity: number;
  unit?: string;
  purchase_unit_price: number;
  purchase_total_price: number;
  purchase_currency?: string;
  supplier_id?: number;
  supplier_name?: string;
  batch_no?: string;
  production_date?: string;
  expire_date?: string;
  warehouse_id?: number;
  warehouse_location?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: number;
}

// 分组数据接口
export interface SupplierGroup {
  supplier_id?: number;
  supplier_name: string;
  items: PurchaseItem[];
  total_quantity: number;
  total_amount: number;
}

export interface PurchaseOrderGroup {
  purchase_order_id?: number;
  purchase_order_no: string;
  supplier_name?: string;
  items: PurchaseItem[];
  total_quantity: number;
  total_amount: number;
}

export interface SkuGroup {
  sku: string;
  product_name: string;
  items: PurchaseItem[];
  total_quantity: number;
  total_amount: number;
}

/**
 * 获取采购明细列表
 */
export async function getPurchaseItems(shipmentId: number, groupBy?: 'supplier' | 'purchase_order' | 'sku') {
  return requestClient.get<PurchaseItem[] | SupplierGroup[] | PurchaseOrderGroup[] | SkuGroup[]>(
    `/v1/logistics/shipments/${shipmentId}/purchase-items`,
    {
      params: groupBy ? { group_by: groupBy } : {},
    }
  );
}

/**
 * 获取采购明细详情
 */
export async function getPurchaseItemDetail(shipmentId: number, itemId: number) {
  return requestClient.get<PurchaseItem>(
    `/v1/logistics/shipments/${shipmentId}/purchase-items/${itemId}`
  );
}

/**
 * 创建采购明细
 */
export async function createPurchaseItem(shipmentId: number, data: Partial<PurchaseItem>) {
  return requestClient.post<PurchaseItem>(
    `/v1/logistics/shipments/${shipmentId}/purchase-items`,
    data
  );
}

/**
 * 更新采购明细
 */
export async function updatePurchaseItem(shipmentId: number, itemId: number, data: Partial<PurchaseItem>) {
  return requestClient.put<PurchaseItem>(
    `/v1/logistics/shipments/${shipmentId}/purchase-items/${itemId}`,
    data
  );
}

/**
 * 删除采购明细
 */
export async function deletePurchaseItem(shipmentId: number, itemId: number) {
  return requestClient.delete(
    `/v1/logistics/shipments/${shipmentId}/purchase-items/${itemId}`
  );
}

/**
 * 重新计算商品明细
 */
export async function recalculatePurchaseItems(shipmentId: number) {
  return requestClient.post(
    `/v1/logistics/shipments/${shipmentId}/purchase-items/recalculate`
  );
}

/**
 * 验证数据一致性
 */
export async function validateShipmentConsistency(shipmentId: number) {
  return requestClient.get<{
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  }>(`/v1/logistics/shipments/${shipmentId}/validate`);
}

