import { requestClient } from '#/api/request';

export interface CustomsProduct {
  id: number;
  name: string;
  hs_code: string;
  rebate_rate?: number;
  unit?: string;
  elements?: string;
  description?: string;
  is_active: boolean;
}

export const getCustomsProductList = (params?: any) => {
  return requestClient.get<{ items: CustomsProduct[]; total: number }>('/v1/customs/products', { params });
};

export const createCustomsProduct = (data: Partial<CustomsProduct>) => {
  return requestClient.post<CustomsProduct>('/v1/customs/products', data);
};

export const updateCustomsProduct = (id: number, data: Partial<CustomsProduct>) => {
  return requestClient.put<CustomsProduct>(`/v1/customs/products/${id}`, data);
};

export const deleteCustomsProduct = (id: number) => {
  return requestClient.delete<void>(`/v1/customs/products/${id}`);
};

