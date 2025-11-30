export interface SysSupplier {
  id: number;
  code: string;
  name: string;
  short_name?: string;
  supplier_type: string;
  status: string;
  grade?: string;

  // 联系信息
  country?: string;
  province?: string;
  city?: string;
  address?: string;
  website?: string;
  primary_contact?: string;
  primary_phone?: string;
  primary_email?: string;
  
  contacts?: Array<{
    name: string;
    role?: string;
    phone?: string;
    email?: string;
  }>;

  // 财务信息
  tax_id?: string;
  currency: string;
  payment_terms?: string;
  payment_method?: string;
  
  bank_accounts?: Array<{
    bank_name: string;
    account: string;
    currency: string;
    swift?: string;
    purpose?: string;
  }>;

  // 运营信息
  lead_time_days?: number;
  moq?: string;
  purchase_uid?: number;
  notes?: string;
  tags?: string[];
  
  created_at?: string;
  updated_at?: string;
}

export interface PaginationParams {
  page: number;
  per_page: number;
  q?: string;
  [key: string]: any;
}
