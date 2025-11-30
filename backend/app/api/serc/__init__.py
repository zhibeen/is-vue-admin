from apiflask import APIBlueprint
from .foundation import serc_foundation_bp
from .finance import serc_finance_bp

# 定义 SERC 总 Blueprint
# prefix: /api/v1/serc
serc_bp = APIBlueprint('serc', __name__, url_prefix='/serc')

# 注册子模块
# /api/v1/serc/foundation
serc_bp.register_blueprint(serc_foundation_bp)
# /api/v1/serc/finance
serc_bp.register_blueprint(serc_finance_bp)
