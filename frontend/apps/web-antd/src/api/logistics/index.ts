/**
 * 发货单相关API
 */
import { requestClient } from '#/api/request';
import type {
  ShipmentOrder,
  ShipmentOrderCreateParams,
  ShipmentOrderUpdateParams,
  GenerateContractsResult,
} from './types';

/**
 * 获取发货单列表
 */
export async function getShipmentListApi(params: {
  page?: number;
  per_page?: number;
  q?: string;
}) {
  return requestClient.get<{
    items: ShipmentOrder[];
    total: number;
    page: number;
    per_page: number;
  }>('/v1/logistics/shipments', { params });
}

/**
 * 获取发货单详情
 */
export async function getShipmentDetailApi(id: number) {
  return requestClient.get<ShipmentOrder>(`/v1/logistics/shipments/${id}`);
}

/**
 * 创建发货单
 */
export async function createShipmentApi(data: ShipmentOrderCreateParams) {
  return requestClient.post<ShipmentOrder>('/v1/logistics/shipments', data);
}

/**
 * 更新发货单
 */
export async function updateShipmentApi(id: number, data: ShipmentOrderUpdateParams) {
  return requestClient.put<ShipmentOrder>(`/v1/logistics/shipments/${id}`, data);
}

/**
 * 删除发货单
 */
export async function deleteShipmentApi(id: number) {
  return requestClient.delete(`/v1/logistics/shipments/${id}`);
}

/**
 * 生成交付合同
 */
export async function generateContractsApi(shipmentId: number) {
  return requestClient.post<GenerateContractsResult>(
    `/v1/logistics/shipments/${shipmentId}/generate-contracts`
  );
}

