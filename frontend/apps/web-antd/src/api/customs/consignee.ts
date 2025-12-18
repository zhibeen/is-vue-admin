import { requestClient } from '#/api/request';

export interface OverseasConsignee {
  id: number;
  name: string;
  address?: string;
  contact_info?: string;
  country?: string;
  is_active: boolean;
}

export const getOverseasConsigneeList = () => {
  return requestClient.get<OverseasConsignee[]>('/v1/customs/consignees');
};

export const createOverseasConsignee = (data: Partial<OverseasConsignee>) => {
  return requestClient.post<OverseasConsignee>('/v1/customs/consignees', data);
};

export const updateOverseasConsignee = (id: number, data: Partial<OverseasConsignee>) => {
  return requestClient.put<OverseasConsignee>(`/v1/customs/consignees/${id}`, data);
};

