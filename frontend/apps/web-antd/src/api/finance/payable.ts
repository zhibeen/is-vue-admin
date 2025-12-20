/**
 * 财务应付单 API
 */
import { requestClient } from '#/api/request';

/**
 * 财务应付单接口
 */
export interface FinPayable {
  id: number;
  payable_no: string;
  source_type: 'logistics' | 'supply_contract' | 'expense';
  source_id: number;
  source_no?: string;
  supplier_id: number;
  supplier_name?: string;
  amount: number;
  currency: string;
  due_date?: string;
  status: 'pending_approval' | 'approved' | 'in_pool' | 'paid';
  approved_by_id?: number;
  approved_at?: string;
  payment_pool_id?: number;
  paid_at?: string;
  paid_amount?: number;
  notes?: string;
  created_at: string;
}

/**
 * 应付单查询参数
 */
export interface PayableQueryParams {
  page?: number;
  per_page?: number;
  source_type?: string;
  status?: string;
  supplier_id?: number;
}

/**
 * 获取应付单列表
 */
export function getPayableListApi(params?: PayableQueryParams) {
  return requestClient.get<FinPayable[]>('/serc/finance/payables', {
    params,
  });
}

/**
 * 获取应付单详情
 */
export function getPayableDetailApi(id: number) {
  return requestClient.get<FinPayable>(`/serc/finance/payables/${id}`);
}

/**
 * 批准应付单
 */
export function approvePayableApi(id: number) {
  return requestClient.post(`/serc/finance/payables/${id}/approve`, {});
}

/**
 * 加入付款池
 */
export function addToPoolApi(id: number) {
  return requestClient.post(`/serc/finance/payables/${id}/add-to-pool`, {});
}

/**
 * 标记为已付款
 */
export function markAsPaidApi(id: number, data: { paid_amount: number }) {
  return requestClient.post(`/serc/finance/payables/${id}/mark-paid`, data);
}

