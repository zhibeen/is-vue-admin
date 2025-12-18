/**
 * 开票合同相关API
 */
import { requestClient } from '#/api/request';
import type {
  SupplyContract,
  SupplyContractCreateParams,
  SupplierTaxInvoice,
  SupplierTaxInvoiceCreateParams,
} from './types';

/**
 * 获取开票合同列表
 */
export async function getSupplyContractListApi() {
  return requestClient.get<SupplyContract[]>('/v1/supply/supply-contracts');
}

/**
 * 获取开票合同详情
 */
export async function getSupplyContractDetailApi(id: number) {
  return requestClient.get<SupplyContract>(`/v1/supply/supply-contracts/${id}`);
}

/**
 * 创建开票合同
 */
export async function createSupplyContractApi(data: SupplyContractCreateParams) {
  return requestClient.post<SupplyContract>('/v1/supply/supply-contracts', data);
}

/**
 * 创建供应商发票
 */
export async function createSupplierInvoiceApi(data: SupplierTaxInvoiceCreateParams) {
  return requestClient.post<SupplierTaxInvoice>('/v1/finance/supplier-invoices', data);
}

/**
 * 获取供应商发票列表
 */
export async function getSupplierInvoiceListApi() {
  return requestClient.get<SupplierTaxInvoice[]>('/v1/finance/supplier-invoices');
}

