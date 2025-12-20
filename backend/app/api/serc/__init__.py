from apiflask import APIBlueprint
from .foundation import serc_foundation_bp
from .finance import serc_finance_bp
from .finance_routes import bp as serc_finance_supply_bp
from .tax_routes import bp as serc_tax_bp
from .payable_routes import payable_bp, payment_pool_bp

# 定义 SERC 总 Blueprint
# prefix: /api/v1/serc
serc_bp = APIBlueprint('serc', __name__, url_prefix='/serc')

# 注册子模块
# /api/v1/serc/foundation
serc_bp.register_blueprint(serc_foundation_bp)
# /api/v1/serc/finance (Original Finance routes)
serc_bp.register_blueprint(serc_finance_bp)
# /api/v1/serc/finance/supply-contracts (New Supply Contract routes)
serc_bp.register_blueprint(serc_finance_supply_bp)
# /api/v1/serc/tax (New Tax routes)
serc_bp.register_blueprint(serc_tax_bp)
# /api/v1/serc/finance/payables (应付单管理)
serc_bp.register_blueprint(payable_bp)
# /api/v1/serc/finance/payment-pools (付款池管理)
serc_bp.register_blueprint(payment_pool_bp)
