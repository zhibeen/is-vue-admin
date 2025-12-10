import { requestClient } from '#/api/request';

// --- Types ---

export interface Product {
  id: number;
  spu_code: string;
  name: string;
  category_id: number;
  category_name?: string;
  brand: string;
  model: string;
  year: string;
  is_active: boolean;
  variants_count?: number;
  created_at?: string;
  updated_at?: string;
  // Detail only
  attributes?: Record<string, any>;
  variants?: ProductVariant[];
}

export interface ProductVariant {
  id?: number;
  sku: string;
  feature_code?: string;
  specs: Record<string, any>;
  price?: number;
  cost_price?: number;
  weight?: number;
  hs_code_id?: number;
    is_active?: boolean;
}

// 新增: Sku 类型定义 (用于列表展示)
export interface Sku {
  sku: string;
  feature_code: string;
  product_id: number;
  product_name: string;
  spu_code: string;
  category_id: number;
  category_name: string;
  brand?: string;
  model?: string;
  attributes_display: string;
  stock_quantity?: number;
  safety_stock?: number;
  in_transit?: number;
  warning_status?: 'normal' | 'warning' | 'danger';
  quality_type?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

// 新增: SkuDetail 类型定义 (用于详情展示)
export interface SkuDetail extends Sku {
  attributes: Record<string, any>;
  compliance_info?: {
    hs_code?: string;
    declared_name?: string;
    declared_unit?: string;
    net_weight?: number;
    gross_weight?: number;
    package_dimensions?: string;
  };
  coding_rules?: {
    category_code?: string;
    vehicle_code?: string;
    serial?: string;
    suffix?: string;
  };
  reference_codes?: Array<{
    code: string;
    code_type: string;
    brand?: string;
  }>;
  fitments?: Array<{
    make?: string;
    model?: string;
    sub_model?: string;
    year_start?: number;
    year_end?: number;
    position?: string;
  }>;
}

// 新增: SkuSearchParams 类型定义
export interface SkuSearchParams {
  page?: number;
  per_page?: number;
  q?: string; // 搜索关键词
  category_id?: number;
  brand?: string;
  model?: string;
  attribute_filters?: Record<string, any>;
  stock_min?: number;
  stock_max?: number;
  is_active?: boolean;
}

export interface ProductSearchParams {
  page?: number;
  pageSize?: number; // Vben/Vxe often use pageSize
  spu_code?: string;
  name?: string;
  category_id?: number;
}

// 新增: CategoryAttribute 类型定义
export interface CategoryAttribute {
  id: string;
  key: string;
  label: string;
  name_en?: string;
  description?: string;
  type: string; // text, textarea, number, boolean, select
  group_name?: string;
  allow_custom?: boolean;
  code_weight?: number;
  options?: Array<{ label: string; value: any }> | string[];
  is_global?: boolean;
  include_in_code?: boolean;
}

// 新增: Category 类型定义
export interface Category {
  id: number;
  name: string;
  name_en?: string;
  code: string;
  abbreviation?: string;
  business_type?: string;
  spu_config?: Record<string, any>;
  parent_id?: number;
  description?: string;
  icon?: string;
  is_active: boolean;
  sort_order: number;
  is_leaf: boolean;
  level?: number;
  children?: Category[];
}

// 新增: CategoryAttributeMapping 类型定义
export interface CategoryAttributeMapping {
  category_id: number;
  attribute_id: number;
  is_required: boolean;
  display_order: number;
  include_in_code?: boolean;
  options?: any;
  group_name?: string;
  attribute_scope?: string;
  allow_custom?: boolean;
  attribute?: CategoryAttribute;
}

// 新增: EffectiveAttribute 类型定义
export interface EffectiveAttribute extends CategoryAttribute {
  origin: 'self' | 'inherited';
  origin_category_id?: number;
  origin_category_name?: string;
  editable: boolean;
  display_order: number;
  is_required: boolean;
  include_in_code?: boolean;
  group_name?: string;
  attribute_scope?: string;
  override_options?: any;
  effective_options?: any;
}

// --- APIs ---

enum Api {
  Products = '/v1/products',
  Categories = '/v1/categories',
  Vehicles = '/v1/vehicles',
  Aux = '/v1/products/aux',
  Attributes = '/v1/categories/attributes',
  AttributeDefinitions = '/v1/categories/attributes/definitions',
}

// Product APIs
export const getProductList = (params: ProductSearchParams) => {
  return requestClient.get<{ items: Product[]; total: number }>(Api.Products, { params });
};

export const getProduct = (id: number) => {
  return requestClient.get<Product>(`${Api.Products}/${id}`);
};

export const createProduct = (data: any) => {
  return requestClient.post<Product>(Api.Products, data);
};

export const updateProduct = (id: number, data: any) => {
  return requestClient.put<Product>(`${Api.Products}/${id}`, data);
};

export const deleteProduct = (id: number) => {
  return requestClient.delete(`${Api.Products}/${id}`);
};

// Category APIs
export const getCategoriesApi = () => {
    return requestClient.get<Category[]>(`${Api.Categories}/tree`);
};

export const createCategoryApi = (data: Partial<Category>) => {
  return requestClient.post<Category>(Api.Categories, data);
};

export const updateCategoryApi = (id: number, data: Partial<Category>) => {
  return requestClient.put<Category>(`${Api.Categories}/${id}`, data);
};

export const deleteCategoryApi = (id: number) => {
  return requestClient.delete(`${Api.Categories}/${id}`);
};

export const migrateCategoryApi = (id: number) => {
  return requestClient.post<Category>(`${Api.Categories}/${id}/migrate`);
};

// Category Attribute APIs
export const getCategoryAttributesApi = (categoryId: number, params?: { inheritance?: boolean }) => {
  return requestClient.get<EffectiveAttribute[]>(`${Api.Categories}/${categoryId}/attributes`, { params });
};

export const addCategoryAttributeApi = (categoryId: number, data: Partial<CategoryAttributeMapping>) => {
  return requestClient.post<CategoryAttributeMapping>(`${Api.Categories}/${categoryId}/attributes`, data);
};

export const updateCategoryAttributeApi = (categoryId: number, attributeId: number, data: Partial<CategoryAttributeMapping>) => {
  return requestClient.put<CategoryAttributeMapping>(`${Api.Categories}/${categoryId}/attributes/${attributeId}`, data);
};

export const removeCategoryAttributeApi = (categoryId: number, attributeId: number) => {
  return requestClient.delete(`${Api.Categories}/${categoryId}/attributes/${attributeId}`);
};

export const copyCategoryAttributesApi = (categoryId: number, sourceCategoryId: number) => {
  return requestClient.post<EffectiveAttribute[]>(`${Api.Categories}/${categoryId}/attributes/copy_from/${sourceCategoryId}`);
};

export const getAllCategoryAttributesMappingsApi = () => {
  return requestClient.get<CategoryAttributeMapping[]>(`${Api.Categories}/attributes/mappings`);
};

// Attribute Definition APIs
export const getAttributeDefinitionsApi = () => {
  return requestClient.get<CategoryAttribute[]>(Api.AttributeDefinitions); 
};

export const createAttributeDefinitionApi = (data: Partial<CategoryAttribute>) => {
  return requestClient.post<CategoryAttribute>(Api.AttributeDefinitions, data);
};

export const updateAttributeDefinitionApi = (id: string, data: Partial<CategoryAttribute>) => {
  return requestClient.put<CategoryAttribute>(`${Api.AttributeDefinitions}/${id}`, data);
};

export const deleteAttributeDefinitionApi = (id: string) => {
  return requestClient.delete(`${Api.AttributeDefinitions}/${id}`);
};

// Dictionary APIs
export const getDictItemsApi = (code: string) => {
    return requestClient.get<any[]>(`/v1/system/dicts/${code}/items`);
};

// Vehicle APIs
export const getVehicleTreeApi = () => {
    return requestClient.get<any[]>(`${Api.Vehicles}/tree`);
};

// Aux APIs
export const previewProductCodesApi = (data: any) => {
    return requestClient.post<any>(`${Api.Aux}/preview`, data);
};

// 新增: 其他缺失的API函数
export const getProductRulesApi = () => {
  return requestClient.get<any>('/v1/product/rules');
};

export const getTaxCategories = () => {
  return requestClient.get<any[]>('/v1/tax/categories');
};

export const getBrandsApi = () => {
  return requestClient.get<any[]>('/v1/vehicles/brands');
};

export const getModelsApi = (brandId?: number) => {
  const params = brandId ? { brand_id: brandId } : undefined;
  return requestClient.get<any[]>('/v1/vehicles/models', { params });
};

export const getYearsApi = (modelId?: number) => {
  const params = modelId ? { model_id: modelId } : undefined;
  return requestClient.get<any[]>('/v1/vehicles/years', { params });
};

export const getProductListApi = (params?: any) => {
  return requestClient.get<{ items: Product[]; total: number }>(Api.Products, { params });
};

// 新增: SKU APIs
export const getSkuListApi = (params?: SkuSearchParams) => {
  return requestClient.get<{ items: Sku[]; total: number }>('/v1/products/variants', { params });
};

export const getSkuDetailApi = (sku: string) => {
  return requestClient.get<SkuDetail>(`/v1/products/variants/${sku}`);
};

export const updateSkuApi = (sku: string, data: Partial<Sku>) => {
  return requestClient.put<Sku>(`/v1/products/variants/${sku}`, data);
};

export const deleteSkuApi = (sku: string) => {
  return requestClient.delete(`/v1/products/variants/${sku}`);
};

export const toggleSkuStatusApi = (sku: string) => {
  return requestClient.post<Sku>(`/v1/products/variants/${sku}/toggle-status`);
};
