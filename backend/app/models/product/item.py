from typing import Optional, List, Dict, Any, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, DECIMAL, Text, DateTime, func, Numeric, Table, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

if TYPE_CHECKING:
    from .category import Category
    from ..serc import SysHSCode
    from ..vehicle import VehicleAux

# --- Existing Helper Tables (SkuSuffix, SysTaxCategory) ---

sku_suffix_categories = Table(
    "sku_suffix_categories",
    db.metadata,
    db.Column("sku_suffix_code", String(5), ForeignKey("sku_suffixes.code"), primary_key=True),
    db.Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)

class SkuSuffix(db.Model):
    __tablename__ = "sku_suffixes"
    code: Mapped[str] = mapped_column(String(5), primary_key=True)
    meaning_en: Mapped[Optional[str]] = mapped_column(String(50))
    meaning_cn: Mapped[Optional[str]] = mapped_column(String(50))
    categories: Mapped[List["Category"]] = relationship(
        "Category", secondary=sku_suffix_categories, backref="sku_suffixes"
    )

class SysTaxCategory(db.Model):
    __tablename__ = "sys_tax_categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    reference_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))

# --- New Product (SPU) Model ---

class Product(db.Model):
    """
    SPU (Standard Product Unit)
    Represents the abstract product, containing common info like name, category, fitment, etc.
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Core Info
    spu_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False, comment="SPU特征码, 如 HL-CHE-SIL-07-13")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    
    # Coding Metadata (JSONB)
    # 汽配存: {"brand": "CHE", "model": "SIL", "year": "07-13"}
    # 通用存: {"series": "Pro", "power": "60W"}
    spu_coding_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, comment="生成SPU码所用的元数据")
    
    # Taxonomy / Attributes
    # attributes: Common attributes shared by all variants (e.g. "Voltage: 12V" if all are 12V)
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={})
    
    # Meta
    description: Mapped[Optional[str]] = mapped_column(Text)
    main_image: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), comment="Brand name if applicable")

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    variants: Mapped[List["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    reference_codes: Mapped[List["ProductReferenceCode"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    
    # Fitments (ACES / TecDoc / General)
    # For now, we keep a simplified fitment table for MVP
    fitments: Mapped[List["ProductFitment"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(SPU) {self.spu_code} - {self.name}>"

# --- New Product Variant (SKU) Model ---

class ProductVariant(db.Model):
    """
    SKU (Stock Keeping Unit)
    Represents the physical sellable item with specific price, stock, specs.
    """
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    
    # Identification
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False, comment="SKU短码 (System Code), 如 101120501DWD")
    
    # Feature Code
    feature_code: Mapped[Optional[str]] = mapped_column(String(200), index=True, comment="SKU特征码 (Business Code), 如 HL-TOY-CAM-20-D-WB")
    
    # Removed: suffix_code, supplier_sku (Cleanup Phase 6)
    # suffix_code: Mapped[Optional[str]] = mapped_column(String(20), comment="生成短码用的后缀, 如 WB")
    # supplier_sku: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Properties
    specs: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={}, comment="Variant specific specs e.g. {color: red}")
    quality_type: Mapped[str] = mapped_column(String(20), default="Aftermarket", comment="OEM, Aftermarket, Refurbished")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Identification (Additional)
    barcode: Mapped[Optional[str]] = mapped_column(String(50), index=True, comment="EAN/UPC")
    image: Mapped[Optional[str]] = mapped_column(String(255), comment="Variant specific image")

    # Commercial
    price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))
    cost_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))
    
    # Physical
    weight: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2), comment="Weight in KG")
    length: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="Length in CM")
    width: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="Width in CM")
    height: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), comment="Height in CM")
    
    # Compliance (Moved from Product/SPU if variants differ, otherwise keep on SPU. Usually SPU level for HS Code)
    # Keeping HS Code on SPU for now or Variant? Let's put on Variant for max flexibility.
    hs_code_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_hs_codes.id"))
    declared_name: Mapped[Optional[str]] = mapped_column(String(200))
    declared_unit: Mapped[Optional[str]] = mapped_column(String(20))
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    hs_code: Mapped["SysHSCode"] = relationship("SysHSCode")

    def __repr__(self):
        return f"<Variant {self.sku}>"

# --- New Reference Codes Table (OE / OEM / Partslink) ---

class ProductReferenceCode(db.Model):
    """
    Stores cross-reference numbers (OE, OEM, Partslink, Hollander)
    """
    __tablename__ = "product_reference_codes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    code_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="OE, OEM, PARTSLINK, HOLLANDER")
    brand: Mapped[Optional[str]] = mapped_column(String(50), comment="Brand of the code e.g. Toyota, Bosch")
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reference_codes")
    
    __table_args__ = (
        Index('idx_ref_code_lookup', 'code', 'code_type'),
    )

# --- Fitment Model (Simplified for now, can be split into ACES/TecDoc later) ---

class ProductFitment(db.Model):
    __tablename__ = "product_fitments"

    id: Mapped[int] = mapped_column(primary_key=True) 
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    
    # Full Fitment Details
    # We can link to a Vehicle table or store raw strings/IDs from ACES
    make: Mapped[Optional[str]] = mapped_column(String(50))
    model: Mapped[Optional[str]] = mapped_column(String(50))
    sub_model: Mapped[Optional[str]] = mapped_column(String(50))
    year_start: Mapped[Optional[int]] = mapped_column(Integer)
    year_end: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Original fields
    vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vehicle_aux.id")) # Keep for backward compat if needed, or remove
    
    position: Mapped[Optional[str]] = mapped_column(String(50)) # e.g. Front Left
    notes: Mapped[Optional[str]] = mapped_column(String(200)) # e.g. "Does NOT Fit Hybrid"
    fitment_type: Mapped[Optional[str]] = mapped_column(String(50)) # e.g. "Classic Body Style"

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="fitments")
    vehicle: Mapped["VehicleAux"] = relationship("VehicleAux")
