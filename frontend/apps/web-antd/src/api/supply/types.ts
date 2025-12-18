/**
 * 开票合同相关类型定义
 */

// 开票合同明细
export interface SupplyContractItem {
  id?: number;
  contract_id?: number;
  product_name: string;
  specification?: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  tax_amount?: number;
  source_delivery_item_ids?: number[];
}

// 开票合同
export interface SupplyContract {
  id: number;
  contract_no: string;
  delivery_contract_id: number;
  supplier_id: number;
  total_amount: number;
  currency: string;
  tax_rate: number;
  total_amount_with_tax: number;
  status: string;
  invoice_status: string;
  invoiced_amount: number;
  notes?: string;
  contract_date: string;
  created_at: string;
  updated_at?: string;
  created_by?: number;
  items: SupplyContractItem[];
}

// 创建开票合同参数
export interface SupplyContractCreateParams {
  delivery_contract_id: number;
  mode: 'auto' | 'manual';
  tax_rate?: number;
  notes?: string;
  contract_date: string;
  items?: SupplyContractItem[];
}

// 供应商发票
export interface SupplierTaxInvoice {
  id: number;
  invoice_no: string;
  invoice_code: string;
  supply_contract_id: number;
  supplier_id: number;
  amount: number;
  tax_amount: number;
  total_amount: number;
  invoice_type: string;
  status: string;
  invoice_date: string;
  received_date?: string;
  attachment_url?: string;
  created_at: string;
  updated_at?: string;
  created_by?: number;
}

// 创建供应商发票参数
export interface SupplierTaxInvoiceCreateParams {
  invoice_no: string;
  invoice_code: string;
  supply_contract_id: number;
  supplier_id: number;
  amount: number;
  tax_amount: number;
  total_amount: number;
  invoice_type: string;
  invoice_date: string;
  received_date?: string;
  attachment_url?: string;
}

