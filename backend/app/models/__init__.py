from .product import Category, AttributeDefinition, CategoryAttribute
from .vehicle import VehicleAux
# Import all new models from product package
from .product import Product, ProductVariant, ProductReferenceCode, ProductFitment, SkuSuffix, ProductVehicle
from .product.rule import ProductBusinessRule
from .user import User, Role, UserRole, Permission, RolePermission
from .data_permission import DataPermissionMeta, RoleDataPermission
from .serc import SysCompany, SysHSCode
from .purchase import SysSupplier
from .supply import ScmSourceDoc, ScmDeliveryContract, ScmDeliveryContractItem
from .serc import SysPaymentTerm
from .system import SysDict
from .customs import CustomsDeclaration, CustomsDeclarationItem

# 导入仓库管理相关模型
from .warehouse import (
    Warehouse, WarehouseLocation, WarehouseStock, WarehouseStockMovement, 
    WarehouseStockDiscrepancy, WarehouseProductGroup, WarehouseProductGroupItem, 
    StockAllocationPolicy
)

# 导入发货单驱动的双轨制合同系统模型
from .logistics import ShipmentOrder, ShipmentOrderItem, ShipmentSource, ShipmentStatus
from .supply.supply_contract import ScmSupplyContract, ScmSupplyContractItem
from .finance import SupplierTaxInvoice