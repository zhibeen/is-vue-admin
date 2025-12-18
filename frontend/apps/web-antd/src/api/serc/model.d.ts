/**
 * SERC System - TypeScript Definitions
 */

// --- Foundation ---
export interface SysPaymentTerm {
  id: number;
  code: string;
  name: string;
  baseline: string;
  days_offset: number;
}

export interface SysSupplier {
  id: number;
  name: string;
  short_name?: string;
  payment_terms?: string; // Snapshot/Legacy
  payment_term_id?: number; // Structured
}

export interface SysCompany {
  id: number;
  // 基础信息
  legal_name: string;
  short_name?: string;
  code?: string; // Added code
  english_name?: string;
  company_type?: string;
  status: string;
  
  // 证照信息
  unified_social_credit_code?: string;
  tax_id?: string;
  business_license_no?: string;
  business_license_issue_date?: string;
  business_license_expiry_date?: string;
  business_scope?: string;
  
  // 地址信息
  registered_address?: string;
  business_address?: string;
  postal_code?: string;
  
  // 联系信息
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;
  fax?: string;
  
  // 财务信息
  bank_accounts?: Array<{
    bank_name: string;
    account_number: string;
    account_name: string;
    swift_code?: string;
    currency: string; // CNY, USD, EUR, etc.
    is_default: boolean;
    purpose: string; // 收付款, 外汇, etc.
  }>;
  tax_rate?: number;
  tax_registration_date?: string;
  
  // 跨境业务
  customs_code?: string;
  /** @deprecated 已合并至海关编码 */
  customs_registration_no?: string;
  /** @deprecated 已合并 */
  inspection_code?: string;
  foreign_trade_operator_code?: string;
  /** @deprecated 已移动至 bank_accounts */
  forex_account?: string;
  /** @deprecated 已取消 */
  forex_registration_no?: string;
  
  // 资质证照
  /** @deprecated 一般贸易无需 */
  import_export_license_no?: string;
  /** @deprecated */
  import_export_license_expiry?: string;
  special_licenses?: Array<{
    type: string;
    license_no: string;
    issue_date: string;
    expiry_date: string;
    issuing_authority: string;
  }>;
  
  // 业务配置
  default_currency?: string;
  default_payment_term?: string;
  credit_limit?: number;
  settlement_cycle?: number;
  cross_border_platform_ids?: Record<string, any>;
  
  // 附件与备注
  attachments?: Array<{
    type: string;
    file_name: string;
    file_url: string;
    upload_date: string;
  }>;
  notes?: string;
  
  // 审计字段
  created_by?: number;
  updated_by?: number;
  created_at?: string;
  updated_at?: string;
}

export interface SysHSCode {
  id: number;
  code: string;
  name: string;
  
  // 计量单位
  unit_1?: string; // 第一法定单位
  unit_2?: string; // 第二法定单位
  default_transaction_unit?: string; // 建议申报单位
  
  // 税率信息
  refund_rate: number;
  import_mfn_rate?: number; // 进口最惠国税率
  import_general_rate?: number; // 进口普通税率
  vat_rate?: number; // 增值税率
  
  // 监管与检疫
  regulatory_code?: string; // 监管条件
  inspection_code?: string; // 检验检疫
  
  // 其他
  elements?: string; // 申报要素
  note?: string;
  updated_at?: string;
}

// --- Supply (L1) ---
export interface ScmDeliveryContractItem {
  product_id: number;
  confirmed_qty: number;
  unit_price: number;
  notes?: string; // Added notes
  // Read-only
  total_price?: number;
  product_name?: string;
}

export interface DeliveryContractCreateReq {
  supplier_id: number;
  company_id?: number; // Added
  currency: 'CNY' | 'USD';
  event_date: string; // YYYY-MM-DD
  
  // Added fields
  delivery_address?: string;
  delivery_date?: string;
  notes?: string;
  payment_term_id?: number; // Structured
  payment_terms?: string; // Optional custom text
  payment_method?: string;
  
  items: ScmDeliveryContractItem[];
}

export interface DeliveryContractDetail {
  id: number;
  contract_no: string;
  supplier_id: number;
  supplier_name?: string;
  
  company_id?: number; // Added
  company_name?: string; // Added (short_name)
  
  total_amount: number;
  paid_amount: number; // Added
  status: 'pending' | 'settling' | 'settled';
  created_at: string;
  event_date?: string; // Added
  
  // Added fields
  delivery_address?: string;
  delivery_date?: string;
  notes?: string;
  payment_terms?: string;
  payment_method?: string;
  
  items: ScmDeliveryContractItem[];
}

export interface DeliveryContractPagination {
  items: DeliveryContractDetail[];
  total: number;
  pages?: number;
  page?: number;
  per_page?: number;
}

export interface ContractSearchParams {
  page?: number;
  per_page?: number;
  contract_no?: string;
  supplier_id?: number;
  company_id?: number; // Added filter
  status?: string;
}

// --- Finance (L2/L3) ---
export interface SOADetailItem {
  id: number;
  l1_contract_id: number;
  l1_contract_no: string;
  amount: number;
  allocated_payment: number;
}

export interface SOAItem {
  id: number;
  soa_no: string;
  supplier_id: number;
  supplier_name: string;
  total_payable: number;
  paid_amount: number;
  invoiced_amount: number;
  payment_status: 'unpaid' | 'partial' | 'paid';
  invoice_status: 'none' | 'partial' | 'full';
  created_at: string;
  details?: SOADetailItem[];
}

export interface SOAGenerateReq {
  l1_ids: number[];
}

export interface PaymentPoolItem {
  id: number;
  soa_id: number;
  soa_no: string;
  amount: number;
  type: 'deposit' | 'balance' | 'prepay' | 'tax';
  status: 'pending_approval' | 'pending_payment' | 'paid';
  priority: number;
  due_date?: string;
  options?: any; 
}

export interface PaymentCreateReq {
  pool_item_ids: number[];
  bank_account: string;
}
