from .routes import warehouse_bp
from .stock import stock_bp
from .virtual import virtual_bp
from .sync import sync_bp
from .third_party import third_party_bp

__all__ = [
    'warehouse_bp',
    'stock_bp',
    'virtual_bp',
    'sync_bp',
    'third_party_bp',
]
