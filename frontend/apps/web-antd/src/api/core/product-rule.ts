import { requestClient } from '#/api/request';

export interface ProductBusinessRule {
  id: number;
  business_type: string;
  name: string;
  generate_strategy: string;
  sku_prefix?: string;
  requires_audit: boolean;
  config?: Record<string, any>;
}

export function getProductRulesApi() {
  return requestClient.get<ProductBusinessRule[]>('/v1/product/rules');
}

export function updateProductRuleApi(id: number, data: Partial<ProductBusinessRule>) {
  return requestClient.put<ProductBusinessRule>(`/v1/product/rules/${id}`, data);
}

