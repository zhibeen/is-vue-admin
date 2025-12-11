export interface Warehouse {
  id: number;
  name: string;
  code: string;
  type: 'physical' | 'virtual' | 'third_party';
  address?: string;
  manager?: string;
  contact_phone?: string;
  is_active: boolean;
  third_party_id?: string;
  config?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface WarehouseCreateInput {
  name: string;
  code: string;
  type: string;
  address?: string;
  manager?: string;
  contact_phone?: string;
  is_active?: boolean;
  third_party_id?: string;
  config?: Record<string, any>;
}

export interface WarehouseUpdateInput extends Partial<WarehouseCreateInput> {}

export interface WarehouseLocation {
  id: number;
  warehouse_id: number;
  code: string;
  name: string;
  type: string;
  is_active: boolean;
  capacity?: number;
  current_usage?: number;
}

export interface Stock {
  id: number;
  warehouse_id: number;
  warehouse_name?: string;
  sku: string;
  product_name?: string;
  quantity: number;
  allocated_quantity: number;
  available_quantity: number;
  batch_no?: string;
  location_id?: number;
  location_code?: string;
  updated_at?: string;
}

export interface StockMovement {
  id: number;
  warehouse_id: number;
  warehouse_name?: string;
  sku: string;
  product_name?: string;
  movement_type: 'in' | 'out' | 'adjust' | 'transfer' | 'allocate' | 'release';
  quantity: number;
  before_quantity: number;
  after_quantity: number;
  reference_no?: string; // order_no
  reference_type?: string; // order_type
  operator_id?: number;
  operator_name?: string;
  created_at: string;
  remark?: string;
}

export interface StockDiscrepancy {
  id: number;
  warehouse_id: number;
  warehouse_name?: string;
  sku: string;
  platform_sku?: string;
  system_qty: number;
  actual_qty: number;
  diff_qty: number;
  status: 'pending' | 'resolved' | 'ignored';
  created_at: string;
  resolved_at?: string;
  resolved_by?: number;
  resolution_note?: string;
}

export interface ThirdPartyWarehouse {
  id: string;
  name: string;
  platform: string;
}

