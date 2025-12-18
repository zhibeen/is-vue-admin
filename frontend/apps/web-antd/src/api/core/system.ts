import { requestClient } from '#/api/request';

/**
 * Permission Definitions
 */
export interface PermissionItem {
  id: number;
  name: string;
  description: string;
}

export interface PermissionAction {
  id: number;
  code: string;
  label: string;
}

export interface PermissionGroup {
  name: string;
  label: string;
  permissions: PermissionAction[];
}

export interface PermissionModule {
  name: string;
  label: string;
  children: PermissionGroup[];
}

/**
 * Data Permission Definitions
 */
export interface DataPermMeta {
  id: number;
  key: string;
  label: string;
  type: 'category' | 'module' | 'resource';
  description?: string;
  children: DataPermMeta[];
}

export interface RoleDataPermConfig {
  category_key: string;
  target_user_ids: number[];
  resource_scopes: Record<string, 'all' | 'custom'>;
}

/**
 * Field Permission Definitions
 */
export interface FieldPermMeta {
  id: number;
  module: string;
  field_key: string;
  label: string;
  description?: string;
}

export interface RoleFieldPermConfig {
  field_key: string;
  is_visible: boolean;
  condition: string; // 'none', 'follower'
}

/**
 * Role Definitions
 */
export interface RoleItem {
  id: number;
  name: string;
  description: string;
  permissions: PermissionItem[];
}

export interface RoleCreateParams {
  name: string;
  description?: string;
  permission_ids: number[];
}

export interface RoleUpdateParams extends RoleCreateParams {}

/**
 * User Definitions
 */
export interface UserItem {
  id: number;
  username: string;
  realname?: string;
  nickname?: string;
  mobile?: string;
  email: string;
  is_active: boolean;
  created_at: string;
  roles: RoleItem[];
}

export interface UserCreateParams {
  username: string;
  email: string;
  password?: string;
  realname?: string;
  nickname?: string;
  mobile?: string;
  role_ids: number[];
  is_active?: boolean;
}

export interface UserUpdateParams extends Partial<UserCreateParams> {}

export interface UserListParams {
  page: number;
  per_page: number;
}

export interface UserListResult {
  items: UserItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

/**
 * API Methods
 */

// Permissions
export const getPermissionsApi = () => {
  return requestClient.get<PermissionItem[]>('/v1/system/permissions');
};

export const getPermissionTreeApi = () => {
  return requestClient.get<PermissionModule[]>('/v1/system/permissions/tree');
};

// Data Permissions
export const getDataPermissionMetasApi = () => {
  return requestClient.get<DataPermMeta[]>('/v1/system/data-permission-metas');
};

export const getRoleDataPermissionApi = (roleId: number, categoryKey: string) => {
  return requestClient.get<RoleDataPermConfig>(`/v1/system/roles/${roleId}/data-permissions`, {
    params: { category_key: categoryKey }
  });
};

export const saveRoleDataPermissionApi = (roleId: number, data: RoleDataPermConfig) => {
  return requestClient.post<RoleDataPermConfig>(`/v1/system/roles/${roleId}/data-permissions`, data);
};

export const saveRoleDataPermissionsBulkApi = (roleId: number, configs: RoleDataPermConfig[]) => {
  return requestClient.post<void>(`/v1/system/roles/${roleId}/data-permissions/bulk`, { configs });
};

// Field Permissions
export const getFieldPermissionMetasApi = () => {
  return requestClient.get<FieldPermMeta[]>('/v1/system/field-permission-metas');
};

export const getRoleFieldPermissionsApi = (roleId: number) => {
  return requestClient.get<RoleFieldPermConfig[]>(`/v1/system/roles/${roleId}/field-permissions`);
};

export const saveRoleFieldPermissionsApi = (roleId: number, configs: RoleFieldPermConfig[]) => {
  return requestClient.post<RoleFieldPermConfig[]>(`/v1/system/roles/${roleId}/field-permissions`, { configs });
};

// Roles
export const getRolesApi = () => {
  return requestClient.get<RoleItem[]>('/v1/system/roles');
};

export const createRoleApi = (data: RoleCreateParams) => {
  return requestClient.post<RoleItem>('/v1/system/roles', data);
};

export const updateRoleApi = (id: number, data: RoleUpdateParams) => {
  return requestClient.put<RoleItem>(`/v1/system/roles/${id}`, data);
};

export const deleteRoleApi = (id: number) => {
  return requestClient.delete<void>(`/v1/system/roles/${id}`);
};

// Users
export const getUsersApi = (params: UserListParams) => {
  return requestClient.get<UserListResult>('/v1/system/users', { params });
};

export const createUserApi = (data: UserCreateParams) => {
  return requestClient.post<UserItem>('/v1/system/users', data);
};

export const updateUserApi = (id: number, data: UserUpdateParams) => {
  return requestClient.put<UserItem>(`/v1/system/users/${id}`, data);
};

export const deleteUserApi = (id: number) => {
  return requestClient.delete<void>(`/v1/system/users/${id}`);
};

// Role Users
export const getRoleUsersApi = (roleId: number, params?: any) => {
  return requestClient.get<UserListResult>(`/v1/system/roles/${roleId}/users`, { params });
};

export const addRoleUsersApi = (roleId: number, userIds: number[]) => {
  return requestClient.post(`/v1/system/roles/${roleId}/users`, { user_ids: userIds });
};

export const removeRoleUserApi = (roleId: number, userId: number) => {
  return requestClient.delete(`/v1/system/roles/${roleId}/users/${userId}`);
};
