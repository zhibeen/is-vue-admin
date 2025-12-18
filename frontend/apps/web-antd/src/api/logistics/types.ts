/**
 * 发货单相关类型定义
 */

// 发货单状态
export enum ShipmentStatus {
  DRAFT = 'draft',
  CONFIRMED = 'confirmed',
  PICKED = 'picked',
  PACKED = 'packed',
  SHIPPED = 'shipped',
  DECLARED = 'declared',
  COMPLETED = 'completed',
}

// 发货单来源
export enum ShipmentSource {
  MANUAL = 'manual',
  EXCEL = 'excel',
  LINGXING = 'lingxing',
  YICANG = 'yicang',
}

// 发货单明细
export interface ShipmentOrderItem {
  id?: number;
  shipment_id?: number;
  product_id?: number;
  sku: string;
  product_name: string;
  product_name_en?: string;
  hs_code?: string;
  customs_product_id?: number;
  quantity: number;
  unit?: string;
  unit_price?: number;
  total_price?: number;
  unit_weight?: number;
  total_weight?: number;
  origin_country?: string;
  external_item_id?: string;
  supplier_id?: number;
}

// 发货单
export interface ShipmentOrder {
  id: number;
  shipment_no: string;
  source: string;
  status: string;
  external_order_no?: string;
  external_tracking_no?: string;
  shipper_company_id: number;
  consignee_id?: number;
  consignee_name?: string;
  consignee_address?: string;
  consignee_country?: string;
  logistics_provider?: string;
  tracking_no?: string;
  shipping_method?: string;
  estimated_ship_date?: string;
  actual_ship_date?: string;
  total_packages?: number;
  total_gross_weight?: number;
  total_net_weight?: number;
  total_volume?: number;
  currency: string;
  total_amount?: number;
  is_declared: boolean;
  is_contracted: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
  created_by?: number;
  items: ShipmentOrderItem[];
}

// 创建发货单参数
export interface ShipmentOrderCreateParams {
  source?: string;
  external_order_no?: string;
  external_tracking_no?: string;
  shipper_company_id: number;
  consignee_id?: number;
  consignee_name?: string;
  consignee_address?: string;
  consignee_country?: string;
  logistics_provider?: string;
  tracking_no?: string;
  shipping_method?: string;
  estimated_ship_date?: string;
  total_packages?: number;
  total_gross_weight?: number;
  total_net_weight?: number;
  total_volume?: number;
  currency?: string;
  total_amount?: number;
  notes?: string;
  items: ShipmentOrderItem[];
}

// 更新发货单参数
export interface ShipmentOrderUpdateParams {
  status?: string;
  logistics_provider?: string;
  tracking_no?: string;
  shipping_method?: string;
  estimated_ship_date?: string;
  actual_ship_date?: string;
  total_packages?: number;
  total_gross_weight?: number;
  total_net_weight?: number;
  total_volume?: number;
  notes?: string;
}

// 生成交付合同结果
export interface GenerateContractsResult {
  success: boolean;
  contract_count: number;
  contracts: Array<{
    id: number;
    contract_no: string;
    supplier_id: number;
    total_amount: number;
  }>;
}

