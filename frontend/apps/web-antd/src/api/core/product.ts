import { requestClient } from '#/api/request';
import type { ProductBusinessRule } from '#/api/core/product-rule';

// --- Interfaces ---

export interface Category {
  id: string;
  parent_id: string | null;
  name: string;
  name_en?: string;     // 英文名称
  code: string;         // SKU数字编码 (3位) - was skuCode
  abbreviation: string; // SPU字符缩写 (如 HL)
  business_type?: 'vehicle' | 'general' | 'electronics'; // 新增
  description?: string;
  icon?: string;
  is_active: boolean;
  sort_order: number;
  is_leaf: boolean;     // was isLeaf
  children?: Category[];
  
  // NEW: Schema Form Config
  spu_config?: {
    template?: string; // SPU 生成模板
    
    // 模式 A: 传统自定义字段
    fields?: {
      key: string;
      label: string;
      type: 'input' | 'select' | 'year_range' | 'number';
      required?: boolean;
      options?: string[] | { label: string; value: any }[];
      placeholder?: string;
    }[];
    
    // 模式 B: 关联车辆层级 (Explicit Level Chain)
    vehicle_link?: {
      enabled: boolean;
      levels: string[]; // e.g. ["brand", "model", "year"]
      root_filter?: string; // Optional: restrict to specific root code
    };
  };
}

export interface Brand {
  id: string;
  name: string;
  code: string;
  abbr: string;
}

export interface Model {
  id: string;
  name: string;
  brand_id: string;
}

export interface VehicleNode {
  id: number;
  parent_id: number | null;
  name: string;
  abbreviation: string; 
  code?: string;
  level_type: 'brand' | 'model' | 'year'; // or custom string
  children?: VehicleNode[];
}

export interface SkuSuffix {
  code: string;
  meaning_cn: string;
  meaning_en: string;
  category_ids?: number[];
}

export interface CategoryAttribute {
  id: string;
  key: string;
  label: string;
  name_en?: string; // New
  description?: string; // New
  type: 'text' | 'number' | 'boolean' | 'select' | 'textarea'; // Added textarea
  // options can be simpler or complex
  options?: { label: string; value: any; code?: string }[]; // Added code
  code_weight?: number; // NEW: 排序权重
  group_name?: string; // NEW: 属性分组
  allow_custom?: boolean; // NEW: 是否允许自定义值
}

export interface CategoryAttributeMapping {
  category_id: number;
  attribute_id: number;
  is_required: boolean;
  display_order: number;
  attribute: CategoryAttribute;
  attribute_scope?: 'spu' | 'sku';
}

export interface TaxCategory {
  id: number;
  code: string;
  name: string;
  short_name?: string;
  reference_rate?: number;
}

export interface Product {
    id: number;
    name: string;
    sku: string;
    spu_code?: string; // NEW
    category_id: number;
    tax_category_id?: number;
    // ... other fields
}

export interface DictItem {
  value: string;
  label: string;
  meta_data?: Record<string, any>;
  sort_order: number;
}

// --- API Functions ---

/**
 * 获取字典项列表
 */
export function getDictItemsApi(dictCode: string) {
  return requestClient.get<DictItem[]>(`/v1/system/dicts/${dictCode}/items`);
}

/**
 * 获取分类树
 */
export function getCategoriesApi() {
  return requestClient.get<Category[]>('/v1/categories/tree');
}

/**
 * 获取品牌列表 (VehiclesAux 基础数据 - 真实车型品牌)
 */
export function getBrandsApi() {
  return requestClient.get<Brand[]>('/v1/vehicles/brands');
}

/**
 * 获取车型列表
 */
export function getModelsApi(brandId: string | number) {
  return requestClient.get<Model[]>(`/v1/vehicles/brands/${brandId}/models`);
}

/**
 * 获取年份列表 (New)
 */
export function getYearsApi(modelId: string | number) {
  return requestClient.get<VehicleNode[]>(`/v1/vehicles/models/${modelId}/years`);
}

/**
 * 获取车辆层级树 (New: Brand -> Model -> Year)
 */
export function getVehicleTreeApi() {
  return requestClient.get<VehicleNode[]>('/v1/vehicles/tree', { timeout: 60000 }); // Increase timeout to 60s
}

/**
 * 获取SKU后缀列表
 */
export function getSkuSuffixesApi() {
  return requestClient.get<SkuSuffix[]>('/v1/products/aux/suffixes');
}

/**
 * 获取分类属性 (Legacy: Per Category)
 */
export function getCategoryAttributesApi(categoryId: string, params?: any) {
  return requestClient.get<CategoryAttribute[]>(`/v1/categories/${categoryId}/attributes`, { params });
}

/**
 * 获取所有分类属性映射 (For Local Filtering)
 */
export function getAllCategoryAttributesMappingsApi() {
  return requestClient.get<CategoryAttributeMapping[]>('/v1/categories/attributes/mappings');
}

/**
 * 获取下一个SKU流水号预览
 */
export function getNextSkuSerialApi(prefix: string) {
  return requestClient.get<{ serial: string }>('/v1/products/aux/next-serial', {
    params: { prefix },
  });
}

/**
 * 预览产品编码 (Preview API)
 */
export function previewProductCodesApi(data: any) {
  return requestClient.post<{ spu_code: string; variants: any[] }>('/v1/products/aux/preview', data);
}

/**
 * 获取税收分类列表
 */
export function getTaxCategories() {
  return requestClient.get<TaxCategory[]>('/v1/products/aux/tax-categories');
}

/**
 * 获取产品列表
 */
export function getProductListApi(params: any) {
  return requestClient.get<{ items: Product[]; total: number }>('/v1/products', { params });
}

/**
 * 创建产品
 */
export function createProduct(data: any) {
  return requestClient.post<Product>('/v1/products', data);
}

/**
 * 创建分类
 */
export function createCategoryApi(data: any) {
  return requestClient.post<Category>('/v1/categories', data);
}

/**
 * 更新分类
 */
export function updateCategoryApi(id: string, data: any) {
  return requestClient.put<Category>(`/v1/categories/${id}`, data);
}

/**
 * 删除分类
 */
export function deleteCategoryApi(id: string) {
  return requestClient.delete<void>(`/v1/categories/${id}`);
}

/**
 * 迁移并更新分类
 */
export function migrateCategoryApi(id: string) {
  return requestClient.post<Category>(`/v1/categories/${id}/migrate`);
}

/**
 * 获取产品业务规则列表
 */
export function getProductRulesApi() {
  return requestClient.get<ProductBusinessRule[]>('/v1/product/rules').then(res => {
    // Handle both direct array or { data: [] } format
    return (res as any).data || res;
  });
}

// --- Attribute Management ---

export function getAttributeDefinitionsApi() {
  return requestClient.get<CategoryAttribute[]>('/v1/categories/attributes/definitions');
}

export function createAttributeDefinitionApi(data: Partial<CategoryAttribute>) {
  return requestClient.post('/v1/categories/attributes/definitions', data);
}

export function updateAttributeDefinitionApi(id: string | number, data: Partial<CategoryAttribute>) {
  return requestClient.put(`/v1/categories/attributes/definitions/${id}`, data);
}

export function deleteAttributeDefinitionApi(id: string | number) {
  return requestClient.delete(`/v1/categories/attributes/definitions/${id}`);
}

export function addCategoryAttributeApi(categoryId: string, data: any) {
  return requestClient.post(`/v1/categories/${categoryId}/attributes`, data);
}

export function updateCategoryAttributeApi(categoryId: string, attributeId: string, data: any) {
  return requestClient.put(`/v1/categories/${categoryId}/attributes/${attributeId}`, data);
}

export function removeCategoryAttributeApi(categoryId: string, attributeId: string) {
  return requestClient.delete(`/v1/categories/${categoryId}/attributes/${attributeId}`);
}

/**
 * 复制属性配置
 */
export function copyCategoryAttributesApi(categoryId: string, sourceCategoryId: string) {
  return requestClient.post(`/v1/categories/${categoryId}/attributes/copy_from/${sourceCategoryId}`);
}
