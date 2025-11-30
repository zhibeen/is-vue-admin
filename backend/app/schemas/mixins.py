from marshmallow import post_dump
from flask import g
from app.services.system_service import SystemService
from app.security import auth

class FieldPermissionMixin:
    """
    Mixin to automatically handle field-level permissions during serialization.
    Usage:
        class ProductSchema(FieldPermissionMixin, Schema):
            cost_price = String(metadata={'permission_key': 'product:cost_price'})
    """

    @post_dump
    def filter_fields(self, data, **kwargs):
        many = self.many
        
        # 1. Check if user is logged in
        try:
            # In testing environment (factory_boy), current_user might not be set
            # or application context might be partial.
            if not auth.current_user:
                return data
            current_user = auth.current_user
        except Exception:
            return data

        # 2. Get user's role (Assume single role for simplicity or take the primary one)
        # In multi-role systems, we usually merge permissions (allow if ANY role allows).
        # Here we simplify: verify against all roles.
        
        # Performance: Cache permissions in g for the duration of the request
        if not hasattr(g, 'field_permission_map'):
            service = SystemService()
            # Fetch all permissions for the user's roles
            # Logic: If ANY role says "visible", it is visible.
            # If ANY role says "hidden", and no role says "visible"? 
            # Standard strategy: Allow > Deny.
            
            # Let's fetch merged config for the user
            g.field_permission_map = service.get_user_merged_field_permissions(current_user.id)

        perm_map = g.field_permission_map

        # 3. Helper function to process a single item
        def process_item(item):
            # Iterate over fields that have metadata defined in the Schema
            # Note: We need access to the Schema instance. `self` is the Schema instance.
            for field_name, field_obj in self.fields.items():
                metadata = field_obj.metadata
                perm_key = metadata.get('permission_key')
                
                if not perm_key:
                    continue
                    
                # Check permission
                config = perm_map.get(perm_key)
                
                # Default is visible if no config exists? 
                # Or default visible if not configured? 
                # Let's assume default is visible.
                if not config:
                    continue
                    
                is_visible = config.get('is_visible', True)
                condition = config.get('condition', 'none')
                
                if not is_visible:
                    # Strategy: Masking or Hiding
                    # For now: Masking to '******'
                    if field_name in item:
                        item[field_name] = '******'
                
                elif condition == 'follower':
                    # Dynamic check
                    # We need the original object to check ownership.
                    # Marshmallow post_dump receives the serialized dict, not the object.
                    # This is tricky in post_dump.
                    # Simplification: If we need row-level context, we might need a different approach
                    # or assume 'follower_id' is present in the serialized item.
                    
                    follower_id = item.get('follower_id')
                    if follower_id != current_user.id:
                        if field_name in item:
                            item[field_name] = '******'

            return item

        # 4. Apply
        if many:
            return [process_item(item) for item in data]
        else:
            return process_item(data)
