/**
 * 发货单物流服务明细API
 */
import { requestClient } from '#/api/request';

export interface ShipmentLogisticsService {
  id: number;
  shipment_id: number;
  logistics_provider_id: number;
  logistics_provider_name?: string;
  service_type: string;
  service_description?: string;
  estimated_amount?: number;
  actual_amount?: number;
  currency: string;
  payment_method?: string;
  service_voucher_id?: number;
  payment_voucher_id?: number;
  status: string;
  confirmed_at?: string;
  reconciled_at?: string;
  paid_at?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface ShipmentLogisticsServiceCreate {
  logistics_provider_id: number;
  service_type: string;
  service_description?: string;
  estimated_amount?: number;
  actual_amount?: number;
  currency?: string;
  payment_method?: string;
  notes?: string;
}

export interface ShipmentLogisticsServiceUpdate {
  logistics_provider_id?: number;
  service_type?: string;
  service_description?: string;
  estimated_amount?: number;
  actual_amount?: number;
  currency?: string;
  payment_method?: string;
  notes?: string;
}

export interface LogisticsCostSummary {
  shipment_id: number;
  total_logistics_cost: number;
  currency: string;
}

/**
 * 获取发货单的物流服务列表
 */
export function getShipmentLogisticsServices(shipmentId: number) {
  return requestClient.get<ShipmentLogisticsService[]>(`/v1/shipments/${shipmentId}/logistics-services`);
}

/**
 * 为发货单添加物流服务
 */
export function addShipmentLogisticsService(
  shipmentId: number,
  data: ShipmentLogisticsServiceCreate
) {
  return requestClient.post<ShipmentLogisticsService>(`/v1/shipments/${shipmentId}/logistics-services`, data);
}

/**
 * 获取物流服务详情
 */
export function getShipmentLogisticsServiceById(
  shipmentId: number,
  serviceId: number
) {
  return requestClient.get<ShipmentLogisticsService>(`/v1/shipments/${shipmentId}/logistics-services/${serviceId}`);
}

/**
 * 更新物流服务
 */
export function updateShipmentLogisticsService(
  shipmentId: number,
  serviceId: number,
  data: ShipmentLogisticsServiceUpdate
) {
  return requestClient.put<ShipmentLogisticsService>(`/v1/shipments/${shipmentId}/logistics-services/${serviceId}`, data);
}

/**
 * 删除物流服务
 */
export function deleteShipmentLogisticsService(
  shipmentId: number,
  serviceId: number
) {
  return requestClient.delete(`/v1/shipments/${shipmentId}/logistics-services/${serviceId}`);
}

/**
 * 确认物流服务
 */
export function confirmShipmentLogisticsService(
  shipmentId: number,
  serviceId: number
) {
  return requestClient.post<ShipmentLogisticsService>(`/v1/shipments/${shipmentId}/logistics-services/${serviceId}/confirm`);
}

/**
 * 获取发货单物流总成本
 */
export function getShipmentLogisticsTotalCost(shipmentId: number) {
  return requestClient.get<LogisticsCostSummary>(`/v1/shipments/${shipmentId}/logistics-services/total-cost`);
}

