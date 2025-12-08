from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class ProductVehicle(db.Model):
    """
    统一的车辆层级数据表 (Brand -> Model -> Series/Year)
    用于 SPU 身份定义和编码生成
    """
    __tablename__ = "product_vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_vehicles.id"), index=True)
    
    # 节点名称，如 "Chevrolet", "Silverado", "2007-2013"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 缩写，用于生成 SPU，如 "CHE", "SIL", "07-13" (原 code)
    abbreviation: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="SPU缩写 (CHE, SIL)")
    
    # 编码，用于官方/行业标准编码，如 "12" (Brand ID), "5890" (Model ID) - 可选
    code: Mapped[Optional[str]] = mapped_column(String(50), index=True, comment="标准编码/ID")
    
    # 层级类型: make, model, year (values from sys_dict:vehicle_level_type)
    level_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="make, model, year")
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 自身关联 (Adjacency List)
    parent: Mapped[Optional["ProductVehicle"]] = relationship(remote_side=[id], backref=db.backref("children", order_by="ProductVehicle.sort_order"))

    def __repr__(self):
        return f"<Vehicle {self.level_type}: {self.name} ({self.abbreviation})>"
