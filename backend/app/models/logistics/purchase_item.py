"""发货单采购明细模型

记录发货单与采购订单的关联关系，用于成本追溯和供应商对账。
"""
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class ShipmentPurchaseItem(db.Model):
    """发货单采购明细表
    
    业务逻辑：
    1. 一个发货单可以包含多个采购订单的商品
    2. 同一SKU可能来自不同的采购批次
    3. 采购明细是唯一的价格数据源
    4. 商品明细通过采购明细自动汇总生成
    """
    __tablename__ = 'shipment_purchase_items'
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 关联关系
    shipment_order_id: Mapped[int] = mapped_column(
        ForeignKey('shipment_orders.id', ondelete='CASCADE'),
        nullable=False,
        comment='发货单ID'
    )
    purchase_order_id: Mapped[int | None] = mapped_column(
        db.Integer,
        nullable=True,
        comment='采购订单ID（关联采购模块）'
    )
    purchase_order_no: Mapped[str | None] = mapped_column(
        db.String(50),
        nullable=True,
        comment='采购订单号'
    )
    purchase_line_id: Mapped[int | None] = mapped_column(
        db.Integer,
        nullable=True,
        comment='采购订单行ID'
    )
    
    # 商品信息
    product_variant_id: Mapped[int] = mapped_column(
        ForeignKey('product_variants.id'),
        nullable=False,
        comment='商品变体ID'
    )
    sku: Mapped[str] = mapped_column(
        db.String(100),
        nullable=False,
        index=True,
        comment='商品SKU'
    )
    product_name: Mapped[str] = mapped_column(
        db.String(200),
        nullable=False,
        comment='商品名称'
    )
    
    # 数量信息
    quantity: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        comment='发货数量'
    )
    unit: Mapped[str] = mapped_column(
        db.String(20),
        default='件',
        comment='单位'
    )
    
    # 价格信息（采购成本）
    purchase_unit_price: Mapped[float] = mapped_column(
        db.Numeric(15, 4),
        nullable=False,
        comment='采购单价'
    )
    purchase_total_price: Mapped[float] = mapped_column(
        db.Numeric(15, 4),
        nullable=False,
        comment='采购总价'
    )
    purchase_currency: Mapped[str] = mapped_column(
        db.String(10),
        default='CNY',
        comment='采购币种'
    )
    
    # 供应商信息
    supplier_id: Mapped[int | None] = mapped_column(
        db.Integer,
        nullable=True,
        comment='供应商ID'
    )
    supplier_name: Mapped[str | None] = mapped_column(
        db.String(200),
        nullable=True,
        comment='供应商名称'
    )
    
    # 批次信息
    batch_no: Mapped[str | None] = mapped_column(
        db.String(50),
        nullable=True,
        comment='采购批次号'
    )
    production_date: Mapped[datetime | None] = mapped_column(
        db.Date,
        nullable=True,
        comment='生产日期'
    )
    expire_date: Mapped[datetime | None] = mapped_column(
        db.Date,
        nullable=True,
        comment='过期日期'
    )
    
    # 仓库信息
    warehouse_id: Mapped[int | None] = mapped_column(
        db.Integer,
        nullable=True,
        comment='仓库ID'
    )
    warehouse_location: Mapped[str | None] = mapped_column(
        db.String(100),
        nullable=True,
        comment='仓库位置'
    )
    
    # 备注
    notes: Mapped[str | None] = mapped_column(
        db.Text,
        nullable=True,
        comment='备注'
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment='创建时间'
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment='更新时间'
    )
    created_by: Mapped[int | None] = mapped_column(
        db.Integer,
        nullable=True,
        comment='创建人ID'
    )
    
    # 关系
    shipment_order: Mapped["ShipmentOrder"] = relationship(
        "ShipmentOrder",
        back_populates="purchase_items"
    )
    product_variant: Mapped["ProductVariant"] = relationship("ProductVariant")
    
    def __repr__(self):
        return f'<ShipmentPurchaseItem {self.sku} x {self.quantity}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'shipment_order_id': self.shipment_order_id,
            'purchase_order_id': self.purchase_order_id,
            'purchase_order_no': self.purchase_order_no,
            'purchase_line_id': self.purchase_line_id,
            'product_variant_id': self.product_variant_id,
            'sku': self.sku,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit': self.unit,
            'purchase_unit_price': float(self.purchase_unit_price),
            'purchase_total_price': float(self.purchase_total_price),
            'purchase_currency': self.purchase_currency,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'batch_no': self.batch_no,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'expire_date': self.expire_date.isoformat() if self.expire_date else None,
            'warehouse_id': self.warehouse_id,
            'warehouse_location': self.warehouse_location,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
        }

