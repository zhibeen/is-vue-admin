from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class SkuSuffix(db.Model):
    __tablename__ = "sku_suffixes"

    code: Mapped[str] = mapped_column(String(5), primary_key=True) # L, R, B
    meaning_en: Mapped[Optional[str]] = mapped_column(String(50))
    meaning_cn: Mapped[Optional[str]] = mapped_column(String(50))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id")) # Optional, if specific to category

    def __repr__(self):
        return f"<SkuSuffix {self.code}>"

class ProductFitment(db.Model):
    __tablename__ = "product_fitments"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicle_aux.id"), primary_key=True)
    notes: Mapped[Optional[str]] = mapped_column(String(200))

    # Relationships
    vehicle: Mapped["VehicleAux"] = relationship("VehicleAux")

class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Identification
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    feature_code: Mapped[Optional[str]] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Taxonomy
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    
    # Variant Logic
    parent_sku_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    suffix_code: Mapped[Optional[str]] = mapped_column(ForeignKey("sku_suffixes.code"))
    
    # Physical Specs
    length: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2))
    width: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2))
    height: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2))
    weight: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2))
    
    # Dynamic Attributes (The Core)
    # Structure: {"voltage": "12V", "lens_color": "Clear"}
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={})
    
    # Search & Meta
    full_text_description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    fitments: Mapped[List["ProductFitment"]] = relationship(backref="product", cascade="all, delete-orphan")
    
    # Self-referential relationship for Variants
    variants: Mapped[List["Product"]] = relationship("Product", 
                                                     backref=db.backref("parent_product", remote_side=[id]),
                                                     foreign_keys=[parent_sku_id])

    def __repr__(self):
        return f"<Product {self.sku} - {self.name}>"

