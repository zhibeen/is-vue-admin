from apiflask import APIBlueprint

# 导入调整后的路径
from .auth.routes import auth_bp
from .product.routes import product_bp
from .product.category import category_bp
from .product.vehicle import vehicle_bp as vehicle_aux_bp
from .product.auxiliary import aux_bp as product_aux_bp
from .product.rule import rule_bp
from .system.dict import system_bp
from .serc import serc_bp  # 导入 SERC
from .purchase import purchase_bp # 导入 Purchase
from .supply import supply_bp # 导入 Supply

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

def register_blueprints(app):
    # 注册 v1 到 app
    app.register_blueprint(api_v1)
