import { requestClient } from '#/api/request';
import type { 
  SOAItem, 
  SOAGenerateReq, 
  PaymentPoolItem, 
  PaymentCreateReq,
  SysPaymentTerm
} from './model';

enum Api {
  SOA = '/v1/serc/finance/soa',
  SOAGenerate = '/v1/serc/finance/soa/generate',
  Pool = '/v1/serc/finance/pool',
  Payment = '/v1/serc/finance/payment',
  PaymentTerms = '/v1/serc/finance/payment-terms',
}

export const getPaymentTerms = () => {
  return requestClient.get<SysPaymentTerm[]>(Api.PaymentTerms);
};

export const getSOAList = (params?: any) => {
  return requestClient.get<SOAItem[]>(Api.SOA, { params });
};

export const generateSOA = (data: SOAGenerateReq) => {
  return requestClient.post<SOAItem>(Api.SOAGenerate, data);
};

export const getPaymentPool = () => {
  return requestClient.get<PaymentPoolItem[]>(Api.Pool);
};

export const createPayment = (data: PaymentCreateReq) => {
  return requestClient.post<any>(Api.Payment, data);
};
