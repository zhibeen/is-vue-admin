import { requestClient } from '#/api/request';

export interface Dict {
  id: string;
  code: string;
  name: string;
  category?: string;
  description?: string;
  is_system: boolean;
  value_options?: Array<{ label: string; value: string }>;
}

export interface DictItem {
  id: string;
  dict_id: string;
  value: string;
  label: string;
  sort_order: number;
  is_active: boolean;
  meta_data?: Record<string, any>;
}

// --- Dict API ---

export function getDictsApi() {
  return requestClient.get<Dict[]>('/v1/system/dicts');
}

export function createDictApi(data: any) {
  return requestClient.post<Dict>('/v1/system/dicts', data);
}

export function updateDictApi(id: string, data: any) {
  return requestClient.put<Dict>(`/v1/system/dicts/${id}`, data);
}

export function deleteDictApi(id: string) {
  return requestClient.delete<void>(`/v1/system/dicts/${id}`);
}

// --- Dict Item API ---

export function getDictItemsApi(dictCode: string) {
  return requestClient.get<DictItem[]>(`/v1/system/dicts/${dictCode}/items`);
}


