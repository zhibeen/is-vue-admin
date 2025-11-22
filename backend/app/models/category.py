from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class CategoryAttribute(db.Model):
    __tablename__ = "category_attributes"

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), primary_key=True)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("attribute_definitions.id"), primary_key=True)
    
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    attribute_definition: Mapped["AttributeDefinition"] = relationship()

class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(10), unique=True) # SKU使用的类目码
    level: Mapped[Optional[int]] = mapped_column(Integer) # 缓存层级
    is_leaf: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(remote_side=[id], backref="children")
    
    # Many-to-Many with Metadata via Association Object
    attributes_association: Mapped[List["CategoryAttribute"]] = relationship(backref="category")
    
    # Products relationship (defined in Product model via string to avoid circular import)
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name} ({self.code})>"

class AttributeDefinition(db.Model):
    __tablename__ = "attribute_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    key_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # internal key: voltage
    label: Mapped[str] = mapped_column(String(100), nullable=False) # display name: 电压
    data_type: Mapped[str] = mapped_column(String(20), nullable=False) # text, number, select, boolean
    options: Mapped[Optional[list]] = mapped_column(JSONB) # ["12V", "24V"]
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"<Attribute {self.key_name}>"

