/**
 * 物流对账单 API
 */
import { requestClient } from '#/api/request';

/**
 * 物流对账单接口
 */
export interface LogisticsStatement {
  id: number;
  statement_no: string;
  logistics_provider_id: number;
  logistics_provider?: {
    id: number;
    provider_name: string;
    provider_code: string;
    service_type: string;
  };
  statement_period_start: string;
  statement_period_end: string;
  total_amount: number;
  currency: string;
  status: 'draft' | 'confirmed' | 'submitted' | 'approved' | 'paid';
  confirmed_by_id?: number;
  confirmed_by?: {
    id: number;
    username: string;
    nickname: string;
  };
  confirmed_at?: string;
  finance_payable_id?: number;
  submitted_to_finance_at?: string;
  attachment_ids?: number[];
  notes?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * 对账单创建请求
 */
export interface StatementCreateRequest {
  logistics_provider_id: number;
  statement_period_start: string;
  statement_period_end: string;
  notes?: string;
  auto_include_services?: boolean;
}

/**
 * 对账单更新请求
 */
export interface StatementUpdateRequest {
  notes?: string;
  attachment_ids?: number[];
}

/**
 * 对账单查询参数
 */
export interface StatementQueryParams {
  page?: number;
  per_page?: number;
  logistics_provider_id?: number;
  status?: string;
  statement_period_start?: string;
  statement_period_end?: string;
}

/**
 * 获取对账单列表
 */
export function getStatementListApi(params?: StatementQueryParams) {
  return requestClient.get<LogisticsStatement[]>('/logistics/statements', {
    params,
  });
}

/**
 * 获取对账单详情
 */
export function getStatementDetailApi(id: number) {
  return requestClient.get<LogisticsStatement>(`/logistics/statements/${id}`);
}

/**
 * 创建对账单
 */
export function createStatementApi(data: StatementCreateRequest) {
  return requestClient.post<LogisticsStatement>('/logistics/statements', data);
}

/**
 * 更新对账单
 */
export function updateStatementApi(id: number, data: StatementUpdateRequest) {
  return requestClient.put<LogisticsStatement>(`/logistics/statements/${id}`, data);
}

/**
 * 删除对账单
 */
export function deleteStatementApi(id: number) {
  return requestClient.delete(`/logistics/statements/${id}`);
}

/**
 * 确认对账单
 */
export function confirmStatementApi(id: number) {
  return requestClient.post<LogisticsStatement>(`/logistics/statements/${id}/confirm`);
}

/**
 * 提交对账单到财务
 */
export function submitStatementToFinanceApi(id: number) {
  return requestClient.post(`/logistics/statements/${id}/submit`, {});
}

/**
 * 添加物流服务到对账单
 */
export function addServiceToStatementApi(id: number, service_id: number) {
  return requestClient.post(`/logistics/statements/${id}/services`, {
    service_id,
  });
}

/**
 * 从对账单移除物流服务
 */
export function removeServiceFromStatementApi(id: number, service_id: number) {
  return requestClient.delete(`/logistics/statements/${id}/services/${service_id}`);
}

