import { requestClient } from '#/api/request';
import type { SysSupplier } from './model';

enum Api {
  Suppliers = '/v1/purchase/suppliers',
}

export const getSupplierList = (params?: any) => {
  return requestClient.get<{ items: SysSupplier[]; total: number; page: number; per_page: number }>(
    Api.Suppliers, 
    { params }
  );
};

export const getSupplierDetail = (id: number) => {
  return requestClient.get<SysSupplier>(`${Api.Suppliers}/${id}`);
};

export const createSupplier = (data: any) => {
  return requestClient.post<SysSupplier>(Api.Suppliers, data);
};

export const updateSupplier = (id: number, data: any) => {
  return requestClient.put<SysSupplier>(`${Api.Suppliers}/${id}`, data);
};

export const deleteSupplier = (id: number) => {
  return requestClient.delete(`${Api.Suppliers}/${id}`);
};
