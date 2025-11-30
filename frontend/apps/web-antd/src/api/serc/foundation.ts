import { requestClient } from '#/api/request';
import type { SysCompany, SysHSCode } from './model';

enum Api {
  Companies = '/v1/serc/foundation/companies',
  HSCodes = '/v1/serc/foundation/hscodes',
}

// Company APIs
export const getCompanyList = () => {
  return requestClient.get<SysCompany[]>(Api.Companies);
};

export const createCompany = (data: any) => {
  return requestClient.post<SysCompany>(Api.Companies, data);
};

export const updateCompany = (id: number, data: any) => {
  return requestClient.put<SysCompany>(`${Api.Companies}/${id}`, data);
};

export const deleteCompany = (id: number) => {
  return requestClient.delete(`${Api.Companies}/${id}`);
};

// HS Code APIs
export const getHSCodeList = () => {
  return requestClient.get<SysHSCode[]>(Api.HSCodes);
};
