from typing import List, Optional
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.user import User, Role, Permission
from app.models.data_permission import DataPermissionMeta, RoleDataPermission
from app.models.field_permission import FieldPermissionMeta, RoleFieldPermission
from app.errors import BusinessError

class SystemService:
    
    # --- Permission Logic ---
    
    def list_permissions(self) -> List[Permission]:
        stmt = select(Permission).order_by(Permission.id)
        return db.session.scalars(stmt).all()

    def get_permission_tree(self) -> dict:
        """
        Parse flat permissions into a structured tree using DB fields.
        Format: Module -> Resource -> Actions
        """
        all_perms = self.list_permissions()
        
        # Constants map
        ACTION_MAP = {
            'view': '查看',
            'manage': '管理',
            'create': '创建',
            'update': '编辑',
            'delete': '删除',
            'import': '导入',
            'export': '导出'
        }
        
        tree = defaultdict(lambda: defaultdict(list))
        
        for perm in all_perms:
            module = perm.module
            resource = perm.resource
            action = perm.action
            
            action_label = ACTION_MAP.get(action, perm.description)
            
            perm_obj = {
                'id': perm.id,
                'code': perm.name,
                'label': action_label
            }
            tree[module][resource].append(perm_obj)
            
        result = []
        for module_key, resources in tree.items():
            children_list = []
            for res_key, perms_list in resources.items():
                children_list.append({
                    'name': res_key,
                    'label': res_key,
                    'permissions': perms_list
                })
            result.append({
                'name': module_key,
                'label': module_key,
                'children': children_list
            })
            
        return {'data': result}

    # --- Data Permission Logic ---

    def get_data_permission_metas(self) -> dict:
        """
        Return structured tree of data permissions.
        L1 (Category) -> L2 (Module) -> L3 (Resource)
        """
        # Fetch all metas
        metas = db.session.scalars(select(DataPermissionMeta).order_by(DataPermissionMeta.sort_order)).all()
        
        # Build tree manually to avoid N+1 or recursion issues if deep
        # Since depth is small (3 levels), we can iterate.
        
        # Map by ID
        meta_map = {m.id: m for m in metas}
        roots = []
        
        # Helper to build dict node
        def to_dict(m):
            return {
                'id': m.id,
                'key': m.key,
                'label': m.label,
                'type': m.type,
                'description': m.description,
                'children': []
            }
            
        # Build hierarchy in memory
        # First pass: create all nodes
        nodes = {m.id: to_dict(m) for m in metas}
        
        # Second pass: link children
        for m in metas:
            if m.parent_id:
                parent = nodes.get(m.parent_id)
                if parent:
                    parent['children'].append(nodes[m.id])
            else:
                roots.append(nodes[m.id])
                
        return {'data': roots}

    def get_role_data_permission(self, role_id: int, category_key: str) -> dict:
        """
        Get role's data permission configuration for a specific category (L1).
        """
        # Ensure role exists
        self.get_role(role_id)
        
        config = db.session.scalar(
            select(RoleDataPermission)
            .where(RoleDataPermission.role_id == role_id)
            .where(RoleDataPermission.category_key == category_key)
        )
        
        if not config:
            return {
                'category_key': category_key,
                'target_user_ids': [],
                'resource_scopes': {}
            }
            
        return {
            'category_key': config.category_key,
            'target_user_ids': config.target_user_ids,
            'resource_scopes': config.resource_scopes
        }

    def save_role_data_permission(self, role_id: int, data: dict):
        """
        Save role's data permission configuration.
        """
        # Ensure role exists
        self.get_role(role_id)
        
        category_key = data['category_key']
        
        config = db.session.scalar(
            select(RoleDataPermission)
            .where(RoleDataPermission.role_id == role_id)
            .where(RoleDataPermission.category_key == category_key)
        )
        
        if not config:
            config = RoleDataPermission(
                role_id=role_id,
                category_key=category_key
            )
            db.session.add(config)
            
        config.target_user_ids = data.get('target_user_ids', [])
        config.resource_scopes = data.get('resource_scopes', {})
        
        db.session.commit()
        return config

    def save_role_data_permissions_bulk(self, role_id: int, configs: List[dict]):
        """
        Bulk save role's data permission configurations in a single transaction.
        """
        self.get_role(role_id)
        
        # Process each config
        for data in configs:
            category_key = data['category_key']
            
            config = db.session.scalar(
                select(RoleDataPermission)
                .where(RoleDataPermission.role_id == role_id)
                .where(RoleDataPermission.category_key == category_key)
            )
            
            if not config:
                config = RoleDataPermission(
                    role_id=role_id,
                    category_key=category_key
                )
                db.session.add(config)
                
            config.target_user_ids = data.get('target_user_ids', [])
            config.resource_scopes = data.get('resource_scopes', {})
        
        db.session.commit()
        return True

    # --- Field Permission Logic ---

    def get_field_permission_metas(self) -> List[FieldPermissionMeta]:
        """Get all field permission definitions."""
        stmt = select(FieldPermissionMeta).order_by(FieldPermissionMeta.module, FieldPermissionMeta.id)
        return db.session.scalars(stmt).all()

    def get_role_field_permissions(self, role_id: int) -> List[RoleFieldPermission]:
        """Get field permission configs for a role."""
        self.get_role(role_id)
        stmt = select(RoleFieldPermission).where(RoleFieldPermission.role_id == role_id)
        return db.session.scalars(stmt).all()

    def save_role_field_permissions(self, role_id: int, configs: List[dict]):
        """Save role's field permission configs."""
        self.get_role(role_id)
        
        existing = db.session.scalars(select(RoleFieldPermission).where(RoleFieldPermission.role_id == role_id)).all()
        existing_map = {p.field_key: p for p in existing}
        
        for config in configs:
            key = config['field_key']
            is_visible = config.get('is_visible', True)
            condition = config.get('condition', 'none')
            
            if key in existing_map:
                # Update
                existing_map[key].is_visible = is_visible
                existing_map[key].condition = condition
            else:
                # Add
                new_perm = RoleFieldPermission(
                    role_id=role_id,
                    field_key=key,
                    is_visible=is_visible,
                    condition=condition
                )
                db.session.add(new_perm)
        
        db.session.commit()
        
        # Return refreshed list
        return self.get_role_field_permissions(role_id)

    def get_user_merged_field_permissions(self, user_id: int) -> dict:
        """
        Get merged field permissions for a user based on all their roles.
        Returns a map: { field_key: { is_visible: bool, condition: str } }
        Strategy: 
        1. Allow > Deny (If any role says visible, it is visible).
        2. Merging conditions is complex. For MVP:
           - If visible is False in ALL roles, then Hidden.
           - If visible in ANY role, check conditions.
           - If merged condition conflict? E.g. Role A: Follower, Role B: None (All).
             -> 'None' (All) is more permissive than 'Follower'. So we take the most permissive.
        """
        user = self.get_user(user_id)
        role_ids = [r.id for r in user.roles]
        
        if not role_ids:
            return {}
            
        # Fetch all configs for these roles
        stmt = select(RoleFieldPermission).where(RoleFieldPermission.role_id.in_(role_ids))
        all_perms = db.session.scalars(stmt).all()
        
        # Group by field_key
        grouped = defaultdict(list)
        for p in all_perms:
            grouped[p.field_key].append(p)
            
        merged = {}
        
        for key, perms in grouped.items():
            # Logic:
            # 1. Is it visible in ANY role?
            #    If a role has NO config for a key, does it mean Visible or Hidden?
            #    Usually default is Visible. But here we only store exceptions?
            #    Wait, our UI saves ALL keys.
            #    Let's assume if record exists, we use it. 
            
            # If any perm is_visible=True and condition='none', then fully visible.
            fully_visible = any(p.is_visible and p.condition == 'none' for p in perms)
            
            if fully_visible:
                merged[key] = {'is_visible': True, 'condition': 'none'}
                continue
                
            # If any perm is_visible=True and condition='follower', then we have at least follower access.
            follower_visible = any(p.is_visible and p.condition == 'follower' for p in perms)
            
            if follower_visible:
                 merged[key] = {'is_visible': True, 'condition': 'follower'}
                 continue
                 
            # If we are here, it means either:
            # - All perms are is_visible=False
            # - Or mixed hidden and nothing?
            
            # If ALL perms explicitly set is_visible=False?
            # Note: We only fetch EXISTING perms. If a user has Role A (Hidden) and Role B (No Config/Default Visible),
            # logic should probably be Visible.
            # But here we are processing only defined perms.
            # We assume for now if defined as hidden, it's hidden, UNLESS another role says visible.
            
            merged[key] = {'is_visible': False, 'condition': 'none'}
            
        return merged

    # --- Role Logic ---

    def list_roles(self) -> List[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).order_by(Role.id)
        return db.session.scalars(stmt).all()

    def get_role(self, role_id: int) -> Role:
        role = db.session.get(Role, role_id, options=[selectinload(Role.permissions)])
        if not role:
            raise BusinessError(status_code=404, message="Role not found")
        return role

    def create_role(self, data: dict) -> Role:
        if db.session.scalar(select(Role).where(Role.name == data['name'])):
            raise BusinessError(message="Role name already exists")

        role = Role(name=data['name'], description=data.get('description'))
        
        if 'permission_ids' in data:
            perms = db.session.scalars(select(Permission).where(Permission.id.in_(data['permission_ids']))).all()
            role.permissions = perms
            
        db.session.add(role)
        db.session.commit()
        return role

    def update_role(self, role_id: int, data: dict) -> Role:
        role = self.get_role(role_id)
        
        if 'name' in data and data['name'] != role.name:
            if db.session.scalar(select(Role).where(Role.name == data['name'])):
                raise BusinessError(message="Role name already exists")
            role.name = data['name']
            
        if 'description' in data:
            role.description = data['description']
            
        if 'permission_ids' in data:
            perms = db.session.scalars(select(Permission).where(Permission.id.in_(data['permission_ids']))).all()
            role.permissions = perms
            
        db.session.commit()
        return role
        
    def delete_role(self, role_id: int):
        role = self.get_role(role_id)
        # Check if users are assigned? Optional protection
        db.session.delete(role)
        db.session.commit()

    def get_role_users(self, role_id: int, page=1, per_page=20, q=None) -> dict:
        role = self.get_role(role_id)
        # 查询该角色下的用户
        stmt = select(User).join(User.roles).where(Role.id == role_id).order_by(User.id.desc())
        
        if q:
            stmt = stmt.where(User.username.ilike(f'%{q}%') | User.email.ilike(f'%{q}%'))
            
        pagination = db.paginate(stmt, page=page, per_page=per_page)
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    def add_users_to_role(self, role_id: int, user_ids: List[int]):
        role = self.get_role(role_id)
        users = db.session.scalars(select(User).where(User.id.in_(user_ids))).all()
        
        for user in users:
            if role not in user.roles:
                user.roles.append(role)
        
        db.session.commit()

    def remove_user_from_role(self, role_id: int, user_id: int):
        role = self.get_role(role_id)
        user = db.session.get(User, user_id)
        
        if user and role in user.roles:
            user.roles.remove(role)
            db.session.commit()

    # --- User Logic ---

    def list_users(self, page=1, per_page=20) -> dict:
        # Simple pagination implementation without separate service method for now
        stmt = select(User).options(selectinload(User.roles)).order_by(User.id.desc())
        
        if per_page <= 0:
            items = db.session.scalars(stmt).all()
            return {
                'items': items,
                'total': len(items),
                'page': 1,
                'per_page': len(items),
                'pages': 1
            }
            
        pagination = db.paginate(stmt, page=page, per_page=per_page)
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    def get_user(self, user_id: int) -> User:
        user = db.session.get(User, user_id, options=[selectinload(User.roles)])
        if not user:
            raise BusinessError(status_code=404, message="User not found")
        return user

    def create_user(self, data: dict) -> User:
        if db.session.scalar(select(User).where(User.username == data['username'])):
            raise BusinessError(message="Username already exists")
        if db.session.scalar(select(User).where(User.email == data['email'])):
            raise BusinessError(message="Email already exists")

        user = User(
            username=data['username'], 
            email=data['email'],
            is_active=data.get('is_active', True)
        )
        user.set_password(data['password'])
        
        if 'role_ids' in data:
            roles = db.session.scalars(select(Role).where(Role.id.in_(data['role_ids']))).all()
            user.roles = roles
            
        db.session.add(user)
        db.session.commit()
        return user

    def update_user(self, user_id: int, data: dict) -> User:
        user = self.get_user(user_id)
        
        if 'username' in data and data['username'] != user.username:
            if db.session.scalar(select(User).where(User.username == data['username'])):
                raise BusinessError(message="Username already exists")
            user.username = data['username']

        if 'email' in data and data['email'] != user.email:
            if db.session.scalar(select(User).where(User.email == data['email'])):
                raise BusinessError(message="Email already exists")
            user.email = data['email']
            
        if 'password' in data and data['password']:
            user.set_password(data['password'])
            
        if 'is_active' in data:
            user.is_active = data['is_active']
            
        if 'role_ids' in data:
            roles = db.session.scalars(select(Role).where(Role.id.in_(data['role_ids']))).all()
            user.roles = roles
            
        db.session.commit()
        return user
        
    def delete_user(self, user_id: int):
        user = self.get_user(user_id)
        db.session.delete(user)
        db.session.commit()
