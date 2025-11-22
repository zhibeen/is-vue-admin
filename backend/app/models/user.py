from datetime import datetime
from typing import List, Optional, Set
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

# --- Association Tables ---

class UserRole(db.Model):
    __tablename__ = "user_roles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)

class RolePermission(db.Model):
    __tablename__ = "role_permissions"
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)

# --- Models ---

class Permission(db.Model):
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True) # e.g. 'product:create'
    description: Mapped[Optional[str]] = mapped_column(String(200))

    def __repr__(self):
        return f"<Permission {self.name}>"

class Role(db.Model):
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True) # admin, editor
    description: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Relationships
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary="role_permissions")

    def __repr__(self):
        return f"<Role {self.name}>"

class User(db.Model):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship("Role", secondary="user_roles")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def role_names(self) -> List[str]:
        return [r.name for r in self.roles]

    @property
    def permissions(self) -> Set[str]:
        """Get all unique permission names from all roles"""
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.name)
        return perms

    def __repr__(self):
        return f"<User {self.username}>"
