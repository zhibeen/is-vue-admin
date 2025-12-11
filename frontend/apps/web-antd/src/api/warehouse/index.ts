import { requestClient } from '#/api/request';

/**
 * 仓库模型
 */
export interface Warehouse {
  id: number;
  code: string;
  name: string;
  category: 'physical' | 'virtual';
  location_type: 'domestic' | 'overseas';
  ownership_type: 'self' | 'third_party';
  status: 'planning' | 'active' | 'suspended' | 'clearing' | 'deprecated';
  business_type: string;
  currency: string;
  timezone: string;
  capacity?: number;
  max_volume?: number;
  contact_person?: string;
  contact_phone?: string;
  address?: string;
  child_warehouse_ids?: number[];
  api_config?: Record<string, any>;
  
  // v1.3/1.4 新增
  third_party_service_id?: number;
  third_party_warehouse_id?: number;
  
  created_at: string;
}

/**
 * 仓库创建/更新参数
 */
export interface WarehouseForm {
  code: string;
  name: string;
  category: string;
  location_type: string;
  ownership_type: string;
  status: string;
  business_type?: string;
  currency?: string;
  timezone?: string;
  capacity?: number;
  max_volume?: number;
  contact_person?: string;
  contact_phone?: string;
  address?: string;
  child_warehouse_ids?: number[];
  api_config?: Record<string, any>;
  
  // v1.3/1.4 新增
  third_party_service_id?: number;
  third_party_warehouse_id?: number;
}

/**
 * 仓库查询参数
 */
export interface WarehouseQuery {
  page?: number;
  per_page?: number;
  keyword?: string;
  category?: string;
  location_type?: string;
  ownership_type?: string;
  status?: string;
}

/**
 * 获取仓库列表
 */
export function getWarehouseList(params: WarehouseQuery) {
  return requestClient.get<{ items: Warehouse[]; total: number }>('/v1/warehouses', { params });
}

/**
 * 获取仓库详情
 */
export function getWarehouseDetail(id: number) {
  return requestClient.get<Warehouse>(`/v1/warehouses/${id}`);
}

/**
 * 创建仓库
 */
export function createWarehouse(data: WarehouseForm) {
  return requestClient.post<Warehouse>('/v1/warehouses', data);
}

/**
 * 更新仓库
 */
export function updateWarehouse(id: number, data: Partial<WarehouseForm>) {
  return requestClient.put<Warehouse>(`/v1/warehouses/${id}`, data);
}

/**
 * 删除仓库
 */
export function deleteWarehouse(id: number) {
  return requestClient.delete(`/v1/warehouses/${id}`);
}

/**
 * 仓库统计数据
 */
export interface WarehouseStats {
  total: number;
  physical: number;
  virtual: number;
  domestic: number;
  overseas: number;
  active: number;
}

/**
 * 获取仓库统计
 */
export function getWarehouseStats() {
  return requestClient.get<WarehouseStats>('/v1/warehouses/stats');
}
