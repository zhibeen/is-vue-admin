import { requestClient } from '#/api/request';

/**
 * 三方服务商
 */
export interface ThirdPartyService {
  id: number;
  name: string;
  code: string;
  provider_code: string; // 4px, winit
  api_url: string;
  app_key?: string;
  // app_secret 不返回
  is_active: boolean;
  status: 'unknown' | 'connected' | 'auth_failed';
  last_sync_time?: string;
}

/**
 * 三方仓库
 */
export interface ThirdPartyWarehouse {
  id: number;
  code: string;
  name: string;
  country_code: string;
  is_active: boolean;
  note?: string;
  last_synced_at: string;
  service_warehouse_name?: string;
  // 兼容字段
  is_bound?: boolean;
  bound_warehouse_name?: string;
}

/**
 * 创建服务商参数
 */
export interface ServiceCreateInput {
  name: string;
  code: string;
  provider_code: string;
  api_url?: string;
  app_key?: string;
  app_secret?: string;
}

/**
 * 远程仓库映射信息
 */
export interface RemoteWarehouse {
  remote_code: string;
  remote_name: string;
  is_bound: boolean;
  local_warehouse_id?: number;
  local_warehouse_name?: string;
}

/**
 * 绑定参数
 */
export interface BindWarehouseInput {
  remote_code: string;
  remote_name: string;
  action: 'create_new' | 'bind_existing';
  local_id?: number;
}

/**
 * 测试连接参数
 */
export interface TestConnectionInput {
  provider_code: string;
  api_url: string;
  app_key: string;
  app_secret: string;
}

/**
 * 测试连接结果
 */
export interface TestConnectionResult {
  success: boolean;
  message?: string;
}

/**
 * 更新服务商参数
 */
export interface ServiceUpdateInput extends Partial<ServiceCreateInput> {
  is_active?: boolean;
}

/**
 * 获取服务商列表
 */
export function getThirdPartyServices() {
  return requestClient.get<ThirdPartyService[]>('/v1/third-party/services');
}

/**
 * 获取服务商详情
 */
export function getThirdPartyService(id: number) {
  return requestClient.get<ThirdPartyService>(`/v1/third-party/services/${id}`);
}

/**
 * 创建服务商
 */
export function createThirdPartyService(data: ServiceCreateInput) {
  return requestClient.post<ThirdPartyService>('/v1/third-party/services', data);
}

/**
 * 更新服务商
 */
export function updateThirdPartyService(id: number, data: ServiceUpdateInput) {
  return requestClient.put<ThirdPartyService>(`/v1/third-party/services/${id}`, data);
}

/**
 * 删除服务商
 */
export function deleteThirdPartyService(id: number) {
  return requestClient.delete(`/v1/third-party/services/${id}`);
}

/**
 * 测试连接
 */
export function testThirdPartyConnection(data: TestConnectionInput) {
  return requestClient.post<TestConnectionResult>('/v1/third-party/test-connection', data);
}

/**
 * 同步远程仓库
 */
export function syncRemoteWarehouses(serviceId: number) {
  return requestClient.post<RemoteWarehouse[]>(`/v1/third-party/services/${serviceId}/sync-warehouses`);
}

/**
 * 绑定仓库
 */
export function bindRemoteWarehouse(serviceId: number, data: BindWarehouseInput) {
  return requestClient.post<{ success: boolean; local_id: number }>(`/v1/third-party/services/${serviceId}/bind-warehouse`, data);
}

// 获取服务商下的仓库列表（轻量级接口）
export function getThirdPartyWarehouses(serviceId: number) {
  return requestClient.get<ThirdPartyWarehouse[]>(`/v1/third-party/services/${serviceId}/warehouses`)
    .then(res => {
      // 添加兼容字段，适配 WarehouseModal.vue 的期望
      return res.map(item => ({
        ...item,
        is_bound: !!item.service_warehouse_name,
        bound_warehouse_name: item.service_warehouse_name
      }));
    });
}

// 兼容旧接口
export function syncThirdPartyWarehouses(serviceId: number) {
    return requestClient.post<any>(`/v1/third-party/services/${serviceId}/sync-warehouses`).then(res => {
        return { synced_count: (res as any[]).length };
    });
}
