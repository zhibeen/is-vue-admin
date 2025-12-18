import { requestClient } from '#/api/request';

enum Api {
  DeclarationList = '/v1/serc/tax/declarations',
  MatchDeclaration = '/v1/serc/tax/match-declaration',
  CheckRisk = '/v1/serc/tax/check-risk',
}

export interface TaxCustomsDeclaration {
  id?: number;
  entry_no: string;
  status?: string;
  export_date?: string;
  destination_country: string;
  fob_total: number;
  exchange_rate: number;
  items?: any[];
  created_at?: string;
}

export interface MatchResponse {
  success: boolean;
  results: MatchResultItem[];
}

export interface ConfirmMatchResponse {
  success: boolean;
  message: string;
}

export interface CancelMatchResponse {
  success: boolean;
  message: string;
}

export interface MatchResultItem {
  item_id: number;
  product_name: string;
  status: string;
  reason: string;
  plan: MatchPlanItem[];
}

export interface MatchPlanItem {
  invoice_item_id: number;
  invoice_no: string;
  take_qty: number;
}

export interface RiskCheckRequest {
  fob_amount: number;
  cost_amount: number;
  currency?: string;
}

export interface RiskCheckResponse {
  is_blocked: boolean;
  reason: string;
  cost: number;
  safe_range: number[];
}

export const getDeclarationList = (params: any) => {
  return requestClient.get<{ items: TaxCustomsDeclaration[]; total: number }>(Api.DeclarationList, { params });
};

export const getDeclarationDetail = (id: number) => {
  return requestClient.get<TaxCustomsDeclaration>(`${Api.DeclarationList}/${id}`);
};

export const createDeclaration = (data: TaxCustomsDeclaration) => {
  return requestClient.post<TaxCustomsDeclaration>(Api.DeclarationList, data);
};

export const matchDeclaration = (id: number) => {
  return requestClient.post<MatchResponse>(`${Api.MatchDeclaration}/${id}`);
};

export const confirmMatch = (id: number) => {
  return requestClient.post<ConfirmMatchResponse>(`${Api.MatchDeclaration}/${id}/confirm`);
};

export const cancelMatch = (id: number) => {
  return requestClient.post<CancelMatchResponse>(`${Api.MatchDeclaration}/${id}/cancel`);
};

export const checkRisk = (data: RiskCheckRequest) => {
  return requestClient.post<RiskCheckResponse>(Api.CheckRisk, data);
};
