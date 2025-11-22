import { requestClient } from '#/api/request';

export interface Brand {
  id: number;
  name: string;
  code: string; // 数字编码
  abbr: string; // 字母缩写
  level_type: 'brand';
}

export interface Model {
  id: number;
  brand_id: number; // Backend returns brand_id
  name: string;
  level_type: 'model';
}

export interface Submodel {
  id: number;
  model_id: number; // Backend returns model_id
  name: string;
  level_type: 'submodel';
}

/**
 * 获取所有品牌
 */
export async function getBrandsApi() {
  return requestClient.get<Brand[]>('/v1/vehiclesaux/brands');
}

/**
 * 创建品牌
 */
export async function createBrandApi(data: { name: string; code: string; abbr: string }) {
  return requestClient.post<Brand>('/v1/vehiclesaux/brands', data);
}

/**
 * 更新品牌
 */
export async function updateBrandApi(id: number, data: { name?: string; code?: string; abbr?: string }) {
  return requestClient.put<Brand>(`/v1/vehiclesaux/brands/${id}`, data);
}

/**
 * 删除品牌
 */
export async function deleteBrandApi(id: number) {
  return requestClient.delete<void>(`/v1/vehiclesaux/brands/${id}`);
}

/**
 * 获取指定品牌下的车型
 */
export async function getModelsApi(brandId: number) {
  return requestClient.get<Model[]>(`/v1/vehiclesaux/brands/${brandId}/models`);
}

/**
 * 创建车型
 */
export async function createModelApi(data: { brand_id: number; name: string }) {
  return requestClient.post<Model>('/v1/vehiclesaux/models', data);
}

/**
 * 更新车型
 */
export async function updateModelApi(id: number, data: { name: string }) {
  return requestClient.put<Model>(`/v1/vehiclesaux/models/${id}`, data);
}

/**
 * 删除车型
 */
export async function deleteModelApi(id: number) {
  return requestClient.delete<void>(`/v1/vehiclesaux/models/${id}`);
}

/**
 * 获取指定车型下的子车型
 */
export async function getSubmodelsApi(modelId: number) {
  return requestClient.get<Submodel[]>(`/v1/vehiclesaux/models/${modelId}/submodels`);
}

/**
 * 创建子车型
 */
export async function createSubmodelApi(data: { model_id: number; name: string }) {
  return requestClient.post<Submodel>('/v1/vehiclesaux/submodels', data);
}

/**
 * 更新子车型
 */
export async function updateSubmodelApi(id: number, data: { name: string }) {
  return requestClient.put<Submodel>(`/v1/vehiclesaux/submodels/${id}`, data);
}

/**
 * 删除子车型
 */
export async function deleteSubmodelApi(id: number) {
  return requestClient.delete<void>(`/v1/vehiclesaux/submodels/${id}`);
}
