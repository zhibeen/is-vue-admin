/**
 * 物流服务商 API
 */
import { requestClient } from '#/api/request';

/**
 * 物流服务商接口
 */
export interface LogisticsProvider {
  id: number;
  provider_name: string;
  provider_code: string;
  service_type: string;
  payment_method?: string;
  settlement_cycle?: string;
  contact_name?: string;
  contact_phone?: string;
  bank_name?: string;
  bank_account?: string;
  is_active: boolean;
}

/**
 * 获取物流服务商列表
 */
export function getProviderListApi(params?: { is_active?: boolean }) {
  return requestClient.get<LogisticsProvider[]>('/logistics/providers', {
    params,
  });
}

/**
 * 获取物流服务商详情
 */
export function getProviderDetailApi(id: number) {
  return requestClient.get<LogisticsProvider>(`/logistics/providers/${id}`);
}

