from apiflask import APIBlueprint

# 导入调整后的路径
from .auth.routes import auth_bp
from .product.routes import product_bp
from .product.category import category_bp
from .product.vehicle import vehicle_bp as vehicle_aux_bp
from .system import system_bp

# 定义 v1 Blueprint
api_v1 = APIBlueprint('api_v1', __name__, url_prefix='/api/v1')

# 注册子模块 (它们不需要再写 /api/v1 前缀)
# 例如 /auth/login -> /api/v1/auth/login
api_v1.register_blueprint(auth_bp)
api_v1.register_blueprint(product_bp)
api_v1.register_blueprint(category_bp)
api_v1.register_blueprint(vehicle_aux_bp)
api_v1.register_blueprint(system_bp)

def register_blueprints(app):
    # 注册 v1 到 app
    app.register_blueprint(api_v1)
