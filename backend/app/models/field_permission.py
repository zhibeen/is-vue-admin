from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class FieldPermissionMeta(db.Model):
    __tablename__ = "field_permission_metas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(50)) # e.g. 'product'
    field_key: Mapped[str] = mapped_column(String(100), unique=True) # e.g. 'product:cost_price'
    label: Mapped[str] = mapped_column(String(100)) # e.g. '采购成本'
    description: Mapped[Optional[str]] = mapped_column(Text)
    
class RoleFieldPermission(db.Model):
    __tablename__ = "role_field_permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    field_key: Mapped[str] = mapped_column(String(100)) # Link to meta key
    
    # is_visible: Boolean. If False, field is hidden (masked with *** or removed)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # condition: 'none' (default), 'follower' (only follower visible)
    # This is an extension for dynamic rules
    condition: Mapped[str] = mapped_column(String(20), default='none') 
    
    # Relationships
    role: Mapped["Role"] = relationship("Role", backref="field_permissions")
