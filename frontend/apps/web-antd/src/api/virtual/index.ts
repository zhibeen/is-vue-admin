import { requestClient } from '#/api/request';

/**
 * 虚拟仓模型
 */
export interface VirtualWarehouse {
  id: number;
  code: string;
  name: string;
  category: 'physical' | 'virtual';
  location_type: 'domestic' | 'overseas';
  ownership_type: 'self' | 'third_party';
  status: 'planning' | 'active' | 'suspended' | 'clearing' | 'deprecated';
  business_type: string;
  currency: string;
  capacity?: number;
  max_volume?: number;
  timezone: string;
  child_warehouse_ids?: number[];
  created_at: string;
}

/**
 * 分配策略模型
 */
export interface AllocationPolicy {
  id: number;
  virtual_warehouse_id: number;
  source_warehouse_id?: number;
  category_id?: number;
  warehouse_product_group_id?: number;
  sku?: string;
  ratio?: number;
  fixed_amount?: number;
  priority: number;
  policy_mode: 'override' | 'inherit';
  effective_from?: string;
  effective_to?: string;
  created_at: string;
}

/**
 * SKU分组模型
 */
export interface ProductGroup {
  id: number;
  code: string;
  name: string;
  note?: string;
  created_at: string;
}

/**
 * SKU分组明细模型
 */
export interface ProductGroupItem {
  group_id: number;
  sku: string;
}

/**
 * 虚拟仓库存计算结果
 */
export interface VirtualStockResult {
  virtual_warehouse_id: number;
  total_physical: number;
  total_available: number;
  total_allocated: number;
  items: Array<{
    sku: string;
    physical_quantity: number;
    available_quantity: number;
    allocated_quantity: number;
    source_warehouse_id?: number;
    allocation_ratio?: number;
  }>;
}

/**
 * 查询参数
 */
export interface PaginationQuery {
  page?: number;
  per_page?: number;
  q?: string;
}

/**
 * 创建/更新策略参数
 */
export interface PolicyForm {
  source_warehouse_id?: number;
  category_id?: number;
  warehouse_product_group_id?: number;
  sku?: string;
  ratio?: number;
  fixed_amount?: number;
  priority: number;
  policy_mode: string;
}

/**
 * 创建/更新SKU分组参数
 */
export interface ProductGroupForm {
  code: string;
  name: string;
  note?: string;
}

/**
 * 添加SKU到分组参数
 */
export interface AddSkuToGroupForm {
  sku: string;
}

// ==================== 虚拟仓相关接口 ====================

/**
 * 获取虚拟仓列表
 */
export function getVirtualWarehouseList(params: PaginationQuery) {
  return requestClient.get<{ items: VirtualWarehouse[]; total: number }>('/v1/virtual', { params });
}

/**
 * 计算虚拟仓库存
 */
export function calculateVirtualStock(virtualWarehouseId: number) {
  return requestClient.get<VirtualStockResult>(`/v1/virtual/${virtualWarehouseId}/stock`);
}

// ==================== 分配策略相关接口 ====================

/**
 * 获取虚拟仓的分配策略列表
 */
export function getPolicyList(virtualWarehouseId: number, params: PaginationQuery) {
  return requestClient.get<{ items: AllocationPolicy[]; total: number }>(`/v1/virtual/${virtualWarehouseId}/policies`, { params });
}

/**
 * 获取分配策略详情
 */
export function getPolicyDetail(id: number) {
  return requestClient.get<AllocationPolicy>(`/v1/virtual/policies/${id}`);
}

/**
 * 创建分配策略
 */
export function createPolicy(virtualWarehouseId: number, data: PolicyForm) {
  return requestClient.post<AllocationPolicy>(`/v1/virtual/${virtualWarehouseId}/policies`, data);
}

/**
 * 更新分配策略
 */
export function updatePolicy(id: number, data: Partial<PolicyForm>) {
  return requestClient.put<AllocationPolicy>(`/v1/virtual/policies/${id}`, data);
}

/**
 * 删除分配策略
 */
export function deletePolicy(id: number) {
  return requestClient.delete(`/v1/virtual/policies/${id}`);
}

// ==================== SKU 分组相关接口 ====================

/**
 * 获取 SKU 分组列表
 */
export function getProductGroupList(params: PaginationQuery) {
  return requestClient.get<{ items: ProductGroup[]; total: number }>('/v1/virtual/product-groups', { params });
}

/**
 * 获取 SKU 分组详情
 */
export function getProductGroupDetail(id: number) {
  return requestClient.get<ProductGroup>(`/v1/virtual/product-groups/${id}`);
}

/**
 * 创建 SKU 分组
 */
export function createProductGroup(data: ProductGroupForm) {
  return requestClient.post<ProductGroup>('/v1/virtual/product-groups', data);
}

/**
 * 更新 SKU 分组
 */
export function updateProductGroup(id: number, data: Partial<ProductGroupForm>) {
  return requestClient.put<ProductGroup>(`/v1/virtual/product-groups/${id}`, data);
}

/**
 * 删除 SKU 分组
 */
export function deleteProductGroup(id: number) {
  return requestClient.delete(`/v1/virtual/product-groups/${id}`);
}

/**
 * 获取分组内的 SKU 列表
 */
export function getGroupSkuList(groupId: number, params: PaginationQuery) {
  return requestClient.get<{ items: ProductGroupItem[]; total: number }>(`/v1/virtual/product-groups/${groupId}/items`, { params });
}

/**
 * 添加 SKU 到分组
 */
export function addSkuToGroup(groupId: number, data: AddSkuToGroupForm) {
  return requestClient.post<ProductGroupItem>(`/v1/virtual/product-groups/${groupId}/items`, data);
}

/**
 * 从分组中移除 SKU
 */
export function removeSkuFromGroup(groupId: number, sku: string) {
  return requestClient.delete(`/v1/virtual/product-groups/${groupId}/items/${sku}`);
}

