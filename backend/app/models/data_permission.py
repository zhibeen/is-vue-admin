from typing import List, Optional, Dict
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db

class DataPermissionMeta(db.Model):
    __tablename__ = "data_permission_metas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("data_permission_metas.id"))
    key: Mapped[str] = mapped_column(String(100), unique=True) # e.g. 'sku', 'sku:product'
    label: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20)) # 'category', 'module', 'resource'
    description: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    children: Mapped[List["DataPermissionMeta"]] = relationship(
        "DataPermissionMeta",
        backref=db.backref("parent", remote_side=[id]),
        order_by="DataPermissionMeta.sort_order"
    )

class RoleDataPermission(db.Model):
    __tablename__ = "role_data_permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    category_key: Mapped[str] = mapped_column(String(100)) # Link to L1 key (e.g. 'sku')
    
    # We use JSONB for flexibility and performance in storing lists/maps
    # target_user_ids: List[int] - The "Permission Users" for this category
    target_user_ids: Mapped[Dict] = mapped_column(JSONB, default=list) 
    
    # resource_scopes: Dict[str, str] - Map of resource_key -> scope_type ('all' or 'custom')
    # e.g. { "sku:product": "all", "warehouse:stock": "custom" }
    resource_scopes: Mapped[Dict] = mapped_column(JSONB, default=dict)
    
    # Relationships
    role: Mapped["Role"] = relationship("Role", backref="data_permissions")
