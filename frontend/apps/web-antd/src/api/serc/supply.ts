import { requestClient } from '#/api/request';
import type { 
  DeliveryContractCreateReq, 
  DeliveryContractDetail, 
  ContractSearchParams,
  DeliveryContractPagination
} from './model';
// 引入 Store 以获取 Token，规避 Mock 拦截 Blob 问题
import { useAccessStore } from '@vben/stores';

enum Api {
  Contracts = '/v1/supply/contracts',
  // PrintContracts = '/v1/supply/contracts/print', // No longer used by axios
}

export const getContractList = (params?: ContractSearchParams) => {
  return requestClient.get<DeliveryContractPagination>(Api.Contracts, { params });
};

export const createManualContract = (data: DeliveryContractCreateReq) => {
  return requestClient.post<DeliveryContractDetail>(Api.Contracts, data);
};

export const printContracts = async (ids: number[]) => {
  // 使用原生 Fetch 彻底绕过 Mock.js 对 XMLHttpRequest 的劫持
  // 获取 Token
  const accessStore = useAccessStore();
  const token = accessStore.accessToken;

  const response = await fetch('/api/v1/supply/contracts/print', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ ids })
  });

  if (!response.ok) {
    throw new Error(`Print failed: ${response.status} ${response.statusText}`);
  }

  return await response.blob();
};

export const exportContracts = async (data: any) => {
  const accessStore = useAccessStore();
  const token = accessStore.accessToken;

  const response = await fetch('/api/v1/supply/contracts/export', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`Export failed: ${response.status} ${response.statusText}`);
  }

  return await response.blob();
};
