from functools import wraps
from apiflask import abort
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask import g
from app.security import auth

def roles_required(*roles):
    """
    Restrict access to users with specific roles.
    Usage: @roles_required('admin', 'editor')
    Note: Must be used with @auth_required or after JWT verification
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Ensure JWT is verified before accessing claims
            verify_jwt_in_request()
            
            claims = get_jwt()
            user_roles = claims.get("roles", [])
            
            has_role = any(role in user_roles for role in roles)
            
            if not has_role:
                abort(403, f"Insufficient permissions. Required roles: {', '.join(roles)}")
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def permission_required(permission_name):
    """
    Restrict access to users with specific atomic permission.
    Usage: @permission_required('product:create')
    Note: Must be used with @auth_required or after JWT verification
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Ensure JWT is verified before accessing claims
            verify_jwt_in_request()
            
            # Check JWT Claims
            claims = get_jwt()
            user_permissions = claims.get("permissions", [])
            
            if permission_name not in user_permissions:
                # Optional: Check if user is Super Admin (bypass all checks)
                user_roles = claims.get("roles", [])
                if 'admin' in user_roles:
                    return fn(*args, **kwargs)
                    
                abort(403, f"Insufficient permissions. Required permission: {permission_name}")
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def admin_required(fn):
    """Shortcut for @roles_required('admin')"""
    return roles_required('admin')(fn)
