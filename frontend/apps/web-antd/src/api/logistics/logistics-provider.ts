/**
 * 物流服务商API
 */
import { requestClient } from '#/api/request';

export interface LogisticsProvider {
  id: number;
  provider_name: string;
  provider_code: string;
  service_type?: string;
  payment_method?: string;
  settlement_cycle?: string;
  contact_name?: string;
  contact_phone?: string;
  contact_email?: string;
  bank_name?: string;
  bank_account?: string;
  bank_account_name?: string;
  service_areas?: string[];
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface LogisticsProviderCreate {
  provider_name: string;
  provider_code: string;
  service_type?: string;
  payment_method?: string;
  settlement_cycle?: string;
  contact_name?: string;
  contact_phone?: string;
  contact_email?: string;
  bank_name?: string;
  bank_account?: string;
  bank_account_name?: string;
  service_areas?: string[];
  is_active?: boolean;
  notes?: string;
}

export interface LogisticsProviderUpdate {
  provider_name?: string;
  service_type?: string;
  payment_method?: string;
  settlement_cycle?: string;
  contact_name?: string;
  contact_phone?: string;
  contact_email?: string;
  bank_name?: string;
  bank_account?: string;
  bank_account_name?: string;
  service_areas?: string[];
  is_active?: boolean;
  notes?: string;
}

/**
 * 获取物流服务商列表
 */
export function getLogisticsProviders(params?: any) {
  return requestClient.get<LogisticsProvider[]>('/v1/logistics-providers', { params });
}

/**
 * 获取物流服务商详情
 */
export function getLogisticsProviderById(id: number) {
  return requestClient.get<LogisticsProvider>(`/v1/logistics-providers/${id}`);
}

/**
 * 创建物流服务商
 */
export function createLogisticsProvider(data: LogisticsProviderCreate) {
  return requestClient.post<LogisticsProvider>('/v1/logistics-providers', data);
}

/**
 * 更新物流服务商
 */
export function updateLogisticsProvider(id: number, data: LogisticsProviderUpdate) {
  return requestClient.put<LogisticsProvider>(`/v1/logistics-providers/${id}`, data);
}

/**
 * 删除物流服务商
 */
export function deleteLogisticsProvider(id: number) {
  return requestClient.delete(`/v1/logistics-providers/${id}`);
}

/**
 * 切换物流服务商启用状态
 */
export function toggleLogisticsProviderStatus(id: number) {
  return requestClient.post<LogisticsProvider>(`/v1/logistics-providers/${id}/toggle`);
}

