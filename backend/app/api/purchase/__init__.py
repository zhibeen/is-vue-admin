from apiflask import APIBlueprint
from .supplier import purchase_supplier_bp

# 定义 Purchase 总 Blueprint
# prefix: /api/v1/purchase
purchase_bp = APIBlueprint('purchase', __name__, url_prefix='/purchase')

# 注册子模块
# /api/v1/purchase/suppliers
purchase_bp.register_blueprint(purchase_supplier_bp)
