from apiflask import APIBlueprint

# 导入调整后的路径
from .auth.routes import auth_bp
from .product.routes import product_bp
from .product.category import category_bp
from .product.vehicle import vehicle_bp as vehicle_aux_bp
from .product.auxiliary import aux_bp as product_aux_bp
from .product.rule import rule_bp
from .system import system_bp
from .serc import serc_bp  # 导入 SERC
from .purchase import purchase_bp # 导入 Purchase
from .supply import supply_bp # 导入 Supply
from .customs import customs_bp # 导入 Customs
from .warehouse import warehouse_bp, stock_bp, virtual_bp, sync_bp, third_party_bp  # 导入仓库管理
from .logistics import logistics_bp # 导入物流管理
from .logistics.purchase_item_routes import purchase_item_bp # 导入采购明细管理
from .logistics.logistics_provider_routes import logistics_provider_bp # 导入物流服务商管理
from .logistics.shipment_logistics_service_routes import shipment_logistics_service_bp # 导入物流服务明细管理
from .logistics.statement_routes import statement_bp # 导入物流对账管理
from .document import document_bp # 导入凭证管理
from .lingxing import lingxing_bp # 导入领星API

# 定义 v1 Blueprint
api_v1 = APIBlueprint('api_v1', __name__, url_prefix='/api/v1')

# 注册子模块 (它们不需要再写 /api/v1 前缀)
# 例如 /auth/login -> /api/v1/auth/login
api_v1.register_blueprint(auth_bp)
api_v1.register_blueprint(product_bp)
api_v1.register_blueprint(category_bp)
api_v1.register_blueprint(vehicle_aux_bp)
api_v1.register_blueprint(product_aux_bp)
api_v1.register_blueprint(rule_bp)
api_v1.register_blueprint(system_bp)
api_v1.register_blueprint(serc_bp)  # 注册 SERC /api/v1/serc/
api_v1.register_blueprint(purchase_bp) # 注册 Purchase /api/v1/purchase/
api_v1.register_blueprint(supply_bp) # 注册 Supply /api/v1/supply/
api_v1.register_blueprint(customs_bp) # 注册 Customs /api/v1/customs/
api_v1.register_blueprint(warehouse_bp) # 注册仓库管理 /api/v1/warehouses/
api_v1.register_blueprint(stock_bp) # 注册库存管理 /api/v1/stocks/
api_v1.register_blueprint(virtual_bp) # 注册虚拟仓管理 /api/v1/virtual/
api_v1.register_blueprint(sync_bp) # 注册同步管理 /api/v1/sync/
api_v1.register_blueprint(third_party_bp) # 注册三方服务商 /api/v1/third-party/
api_v1.register_blueprint(logistics_bp) # 注册物流管理 /api/v1/logistics/
api_v1.register_blueprint(purchase_item_bp) # 注册采购明细管理 /api/v1/logistics/shipments/{id}/purchase-items
api_v1.register_blueprint(logistics_provider_bp) # 注册物流服务商管理 /api/v1/logistics-providers/
api_v1.register_blueprint(shipment_logistics_service_bp) # 注册物流服务明细管理 /api/v1/shipments/{id}/logistics-services/
api_v1.register_blueprint(statement_bp) # 注册物流对账管理 /api/v1/logistics/statements
api_v1.register_blueprint(document_bp) # 注册凭证管理 /api/v1/documents/
api_v1.register_blueprint(lingxing_bp) # 注册领星API /api/v1/lingxing/

def register_blueprints(app):
    # 注册 v1 到 app
    app.register_blueprint(api_v1)
