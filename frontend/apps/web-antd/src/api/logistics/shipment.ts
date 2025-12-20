/**
 * 发货单API接口
 */
import { requestClient } from '#/api/request';

// 发货单列表查询参数
export interface ShipmentListParams {
  page?: number;
  per_page?: number;
  q?: string;
  status?: string;
  source?: string;
  start_date?: string;
  end_date?: string;
}

// 发货单明细
export interface ShipmentItem {
  id?: number;
  sku: string;
  product_name: string;
  hs_code?: string;
  export_name?: string;
  quantity: number;
  unit: string;
  customs_unit?: string;
  unit_price?: number;
  total_price?: number;
  tax_rate?: number;
  tax_amount?: number;
  unit_price_with_tax?: number;
  total_price_with_tax?: number;
  supplier_id?: number;
  supplier_name?: string;
  
  // FBA专用字段
  fnsku?: string;
  msku?: string;
  asin?: string;
  marketplace_listing_id?: string;
  
  // 第三方仓专用字段
  warehouse_matched_qty?: number;
  warehouse_received_qty?: number;
  warehouse_pending_qty?: number;
  shelf_location?: string;
  
  // 包装信息
  package_no?: string;
  barcode?: string;
  unit_volume?: number;
  unit_weight?: number;
  total_weight?: number;
  
  origin_country?: string;
  notes?: string;
}

// 发货单
export interface Shipment {
  id?: number;
  shipment_no?: string;
  source?: string;
  status?: string;
  external_order_no?: string;
  external_tracking_no?: string;
  
  // 基本信息
  shipper_company_id: number;
  shipper_company_name?: string;
  consignee_id?: number;
  consignee_name?: string;
  consignee_address?: string;
  consignee_country?: string;
  
  // 仓库信息
  origin_warehouse_id?: number;
  origin_warehouse_name?: string;
  origin_warehouse_type?: string;
  origin_warehouse_address?: string;
  is_factory_direct?: number;
  destination_warehouse_id?: number;
  destination_warehouse_name?: string;
  destination_warehouse_code?: string;
  destination_warehouse_type?: string; // fba/third_party/self
  destination_warehouse_address?: string;
  
  // FBA专用
  fba_shipment_id?: string;
  fba_center_codes?: string[];
  marketplace?: string;
  
  // 第三方仓专用
  warehouse_service_provider?: string;
  warehouse_contact?: string;
  warehouse_contact_phone?: string;
  
  // 物流信息
  logistics_provider?: string;
  logistics_service_type?: string;
  tracking_no?: string;
  shipping_method?: string;
  freight_term?: string;
  
  // 时间节点
  estimated_ship_date?: string;
  actual_ship_date?: string;
  estimated_arrival_date?: string;
  actual_arrival_date?: string;
  warehouse_received_date?: string;
  completed_date?: string;
  
  // 包装信息
  total_packages?: number;
  packing_method?: string;
  total_gross_weight?: number;
  total_net_weight?: number;
  total_volume?: number;
  volumetric_weight?: number;
  chargeable_weight?: number;
  
  // 财务信息
  currency?: string;
  
  // 物流成本（核心字段）
  freight_cost?: number;
  insurance_cost?: number;
  handling_fee?: number;
  other_costs?: number;
  total_logistics_cost?: number;
  
  // 以下字段已废弃，将在v2.0移除
  /** @deprecated 请从商品明细计算 */
  total_goods_value?: number;
  /** @deprecated 请从报关单获取 */
  declared_value?: number;
  /** @deprecated 请从公司/收货人主表获取 */
  vat_number?: string;
  /** @deprecated 请从税务配置获取 */
  tax_rate?: number;
  /** @deprecated 请从税务系统获取 */
  estimated_tax?: number;
  /** @deprecated 请从税务系统获取 */
  actual_tax?: number;
  /** @deprecated 请从采购明细汇总 */
  total_purchase_cost?: number;
  /** @deprecated 请从财务系统计算 */
  profit_margin?: number;
  /** @deprecated 请从财务配置获取 */
  cost_allocation_method?: string;
  /** @deprecated 仅供参考 */
  total_amount?: number;
  /** @deprecated 仅供参考 */
  total_tax_amount?: number;
  /** @deprecated 仅供参考 */
  total_amount_with_tax?: number;
  
  // 关联状态
  customs_declaration_id?: number;
  is_declared?: number;
  is_contracted?: number;
  
  // 其他
  notes?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: number;
  items?: ShipmentItem[];
}

// 分页响应
export interface ShipmentListResponse {
  items: Shipment[];
  total: number;
  page: number;
  per_page: number;
}

/**
 * 获取发货单列表
 */
export async function getShipmentList(params: ShipmentListParams) {
  return requestClient.get<ShipmentListResponse>('/v1/logistics/shipments', {
    params,
  });
}

/**
 * 获取发货单详情
 */
export async function getShipmentDetail(id: number) {
  return requestClient.get<Shipment>(`/v1/logistics/shipments/${id}`);
}

/**
 * 创建发货单
 */
export async function createShipment(data: Partial<Shipment>) {
  return requestClient.post<Shipment>('/v1/logistics/shipments', data);
}

/**
 * 更新发货单
 */
export async function updateShipment(id: number, data: Partial<Shipment>) {
  return requestClient.put<Shipment>(`/v1/logistics/shipments/${id}`, data);
}

/**
 * 删除发货单
 */
export async function deleteShipment(id: number) {
  return requestClient.delete(`/v1/logistics/shipments/${id}`);
}

/**
 * 确认发货单
 */
export async function confirmShipment(id: number) {
  return requestClient.post<Shipment>(`/v1/logistics/shipments/${id}/confirm`);
}

/**
 * 生成交付合同
 */
export async function generateContracts(id: number) {
  return requestClient.post(`/v1/logistics/shipments/${id}/generate-contracts`);
}

/**
 * 供应商拆分预览
 */
export async function getSuppliersSummary(id: number) {
  return requestClient.get(`/v1/logistics/shipments/${id}/suppliers-preview`);
}

