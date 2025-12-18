import { requestClient } from '#/api/request';

export interface TaxCustomsItem {
  id?: number;
  product_id: number;
  supplier_id?: number;
  sku?: string;
  
  // 基础信息
  item_no?: number;
  hs_code?: string;
  product_name_spec?: string;
  
  // 数量1
  qty: number;
  unit: string;
  
  // 数量1 (法定)
  qty_1?: number;
  unit_1?: string;
  
  // 数量2
  qty_2?: number;
  unit_2?: string;
  
  // 价格
  usd_unit_price: number;
  usd_total: number;
  currency?: string;
  
  // 原产地与目的国
  origin_country?: string;
  final_dest_country?: string;
  district_code?: string;
  exemption_way?: string;
  
  // Packing Info
  box_no?: string;
  net_weight?: number;
  gross_weight?: number;
}

export interface ContractSummary {
  id: number;
  contract_no: string;
  supplier_id: number;
  total_amount: number;
  status: string;
}

export interface TaxCustomsDeclaration {
  id: number;
  status: string;
  
  // 基础信息
  pre_entry_no?: string;
  customs_no?: string;
  filing_no?: string;
  internal_shipper_id?: number;
  internal_shipper_name?: string;
  overseas_consignee?: string;
  
  // 日期与备案
  export_date?: string;
  declare_date?: string;
  
  // 港口与地区
  departure_port?: string;
  entry_port?: string;
  destination_country?: string;
  trade_country?: string;
  loading_port?: string;
  
  // 运输信息
  transport_mode?: string;
  conveyance_ref?: string;
  bill_of_lading_no?: string;
  shipping_no?: string; // Alias for input
  shipping_date?: string;
  
  // 贸易信息
  trade_mode?: string;
  nature_of_exemption?: string;
  license_no?: string;
  contract_no?: string;
  transaction_mode?: string;
  
  // 费用
  freight?: string;
  insurance?: string;
  incidental?: string;
  
  // 包装与重量
  package_type?: string;
  pack_count?: number;
  gross_weight?: number;
  net_weight?: number;
  
  // 备注
  marks_and_notes?: string;
  documents?: string;
  
  // 金额
  fob_total: number;
  exchange_rate: number;
  currency?: string;
  
  // 源数据
  source_type?: string;

  // 货柜模式
  container_mode?: string;

  items?: TaxCustomsItem[];
  contracts?: ContractSummary[];
  created_at?: string;
  
  // 动态字段
  required_file_slots?: string[];
}

export interface DeclarationImportReq {
  file: File;
  shipping_no?: string;
  logistics_provider?: string;
  container_mode?: string;
  export_date?: string;
}

enum Api {
  DeclarationList = '/v1/customs/declarations',
  DeclarationImport = '/v1/customs/declarations/import',
  GenerateContracts = '/v1/customs/declarations', 
}

export const getDeclarationListApi = (params?: any) => {
  return requestClient.get<{ items: TaxCustomsDeclaration[]; total: number }>(Api.DeclarationList, { params });
};

export const getDeclarationDetailApi = (id: number) => {
  return requestClient.get<TaxCustomsDeclaration>(`${Api.DeclarationList}/${id}`);
};

export const updateDeclarationApi = (id: number, data: Partial<TaxCustomsDeclaration>) => {
  return requestClient.put<TaxCustomsDeclaration>(`${Api.DeclarationList}/${id}`, data);
};

export const importDeclarationApi = (data: DeclarationImportReq) => {
  return requestClient.upload<TaxCustomsDeclaration>(Api.DeclarationImport, data);
};

export const generateContractsApi = (id: number) => {
  return requestClient.post<{ contract_ids: number[]; message: string }>(`${Api.GenerateContracts}/${id}/generate-contracts`);
};

export const getDeclarationStatsApi = () => {
  return requestClient.get<{ status: string; count: number; label: string }[]>(`${Api.DeclarationList}/stats`);
};

// 状态流转相关
export interface StatusTransition {
  status: string;
  description: string;
}

export interface AllowedTransitionsResponse {
  current_status: string;
  is_locked: boolean;
  allowed_transitions: StatusTransition[];
}

export const getAllowedTransitionsApi = (id: number) => {
  return requestClient.get<AllowedTransitionsResponse>(`${Api.DeclarationList}/${id}/status`);
};

export const changeDeclarationStatusApi = (id: number, status: string, reason?: string) => {
  return requestClient.post<TaxCustomsDeclaration>(`${Api.DeclarationList}/${id}/status`, { status, reason });
};

// 下载PDF
export interface DownloadPdfRequest {
  includes: string[]; // 包含的内容: declaration, packing, invoice, elements, contract, proxy, files
}

export interface DownloadPdfResponse {
  pdf_base64: string;
  filename: string;
}

export const downloadDeclarationPdfApi = (id: number, includes: string[]) => {
  return requestClient.post<DownloadPdfResponse>(
    `${Api.DeclarationList}/${id}/download-pdf`, 
    { includes },
    { timeout: 60000 } // PDF生成可能需要较长时间
  );
};

// 文件完整性检查
export interface FilesCheckResult {
  is_complete: boolean;
  required_slots: string[];
  missing_slots: string[];
  uploaded_slots: string[];
  missing_count: number;
}

export const checkFilesCompleteApi = (id: number) => {
  return requestClient.get<FilesCheckResult>(
    `${Api.DeclarationList}/${id}/files/check-complete`
  );
};
