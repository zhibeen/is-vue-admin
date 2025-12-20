"""领星API Schema定义"""
from .shipment import (
    ShipmentDetailQuerySchema,
    ShipmentItemSchema,
    ShipmentAddressSchema,
    ShipmentDetailSchema
)
from .stock import (
    StockDetailQuerySchema,
    StockItemSchema,
    StockDimensionsSchema,
    StockDetailSchema
)

__all__ = [
    'ShipmentDetailQuerySchema',
    'ShipmentItemSchema',
    'ShipmentAddressSchema',
    'ShipmentDetailSchema',
    'StockDetailQuerySchema',
    'StockItemSchema',
    'StockDimensionsSchema',
    'StockDetailSchema',
]

