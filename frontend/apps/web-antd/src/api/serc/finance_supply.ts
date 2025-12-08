import { requestClient } from '#/api/request';

enum Api {
  Preview = '/v1/serc/finance/supply-contracts/preview',
  Generate = '/v1/serc/finance/supply-contracts/generate',
}

export interface SupplyContractPreview {
  l1_contract_id: number;
  contract_no: string;
  supplier_name: string;
  l1_total_amount: number;
  preview_total_amount: number;
  diff: number;
  is_balanced: boolean;
  items: SupplyContractItem[];
  warnings: string[];
}

export interface SupplyContractItem {
  invoice_name: string;
  invoice_unit?: string;
  specs?: string;
  quantity: number;
  price_unit: number;
  amount: number;
  tax_rate: number;
  tax_code?: string;
  skus?: string[];
}

export interface GenerateRequest {
  l1_contract_id: number;
  confirmed_items: SupplyContractItem[];
}

export interface SupplyContract {
  id: number;
  contract_no: string;
  status: string;
  total_amount: number;
}

/**
 * 预览 L1.5 供货合同
 */
export const previewSupplyContract = (l1Id: number) => {
  return requestClient.get<SupplyContractPreview>(`${Api.Preview}/${l1Id}`);
};

/**
 * 生成 L1.5 供货合同
 */
export const generateSupplyContract = (data: GenerateRequest) => {
  return requestClient.post<SupplyContract>(Api.Generate, data);
};

