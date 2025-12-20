/**
 * 凭证管理API
 */
import { requestClient } from '#/api/request';

export interface DocumentCenter {
  id: number;
  business_type: string;
  document_type?: string;
  document_category?: string;
  business_id: number;
  business_no?: string;
  file_name: string;
  file_path: string;
  file_size?: number;
  file_type?: string;
  file_url?: string;
  uploaded_by_id: number;
  uploaded_at: string;
  audit_status: string;
  audited_by_id?: number;
  audited_at?: string;
  audit_notes?: string;
  archived: boolean;
  archive_path?: string;
  archived_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface DocumentQueryParams {
  business_type?: string;
  business_id?: number;
  audit_status?: string;
  archived?: boolean;
}

export interface DocumentAudit {
  audit_status: 'approved' | 'rejected';
  audit_notes?: string;
}

/**
 * 上传凭证
 */
export function uploadDocument(formData: FormData) {
  return requestClient.post<DocumentCenter>('/v1/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * 查询凭证列表
 */
export function getDocuments(params: DocumentQueryParams) {
  return requestClient.get<DocumentCenter[]>('/v1/documents', { params });
}

/**
 * 按业务单据查询凭证
 */
export function getDocumentsByBusiness(businessType: string, businessId: number) {
  return requestClient.get<DocumentCenter[]>('/v1/documents', {
    params: {
      business_type: businessType,
      business_id: businessId,
    },
  });
}

/**
 * 获取凭证详情
 */
export function getDocumentById(id: number) {
  return requestClient.get<DocumentCenter>(`/v1/documents/${id}`);
}

/**
 * 删除凭证
 */
export function deleteDocument(id: number) {
  return requestClient.delete(`/v1/documents/${id}`);
}

/**
 * 审核凭证
 */
export function auditDocument(id: number, data: DocumentAudit) {
  return requestClient.post<DocumentCenter>(`/v1/documents/${id}/audit`, data);
}

