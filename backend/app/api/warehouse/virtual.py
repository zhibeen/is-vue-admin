from apiflask import APIBlueprint
from apiflask.views import MethodView
from app.schemas.warehouse import (
    WarehouseSchema, StockAllocationPolicySchema, StockAllocationPolicyCreateSchema,
    StockAllocationPolicyUpdateSchema, WarehouseProductGroupSchema, WarehouseProductGroupCreateSchema,
    WarehouseProductGroupItemSchema, WarehouseProductGroupItemCreateSchema
)
from app.schemas.pagination import make_pagination_schema, PaginationQuerySchema
from app.services.warehouse import VirtualService
from app.security import auth
from app.decorators import permission_required
from flask_jwt_extended import get_jwt_identity

# 虚拟仓管理Blueprint
virtual_bp = APIBlueprint('virtual', __name__, url_prefix='/virtual', tag='虚拟仓管理')

# 创建服务实例
virtual_service = VirtualService()

# 创建分页Schema
VirtualWarehousePaginationSchema = make_pagination_schema(WarehouseSchema)
AllocationPolicyPaginationSchema = make_pagination_schema(StockAllocationPolicySchema)
ProductGroupPaginationSchema = make_pagination_schema(WarehouseProductGroupSchema)


class VirtualWarehouseListAPI(MethodView):
    """虚拟仓列表API"""
    decorators = [virtual_bp.auth_required(auth)]
    
    @virtual_bp.doc(summary='获取虚拟仓列表', description='获取所有虚拟仓列表')
    @virtual_bp.input(PaginationQuerySchema, location='query', arg_name='query_data')
    @virtual_bp.output(VirtualWarehousePaginationSchema)
    @permission_required('virtual:view')
    def get(self, query_data):
        """获取虚拟仓列表"""
        result = virtual_service.get_virtual_warehouses(
            page=query_data['page'],
            per_page=query_data['per_page'],
            keyword=query_data.get('q')
        )
        return result


class VirtualStockAPI(MethodView):
    """虚拟仓库存API"""
    decorators = [virtual_bp.auth_required(auth)]
    
    @virtual_bp.doc(summary='计算虚拟仓库存', description='计算虚拟仓的库存分配情况')
    @virtual_bp.output({'data': {'type': 'object'}})
    @permission_required('virtual:view')
    def get(self, virtual_warehouse_id):
        """计算虚拟仓库存"""
        result = virtual_service.calculate_virtual_stock(virtual_warehouse_id)
        return {'data': result}


class AllocationPolicyListAPI(MethodView):
    """分配策略列表API"""
    decorators = [virtual_bp.auth_required(auth)]
    
    @virtual_bp.doc(summary='获取分配策略列表', description='获取虚拟仓的分配策略列表')
    @virtual_bp.input(PaginationQuerySchema, location='query', arg_name='query_data')
    @virtual_bp.output(AllocationPolicyPaginationSchema)
    @permission_required('virtual:view')
    def get(self, virtual_warehouse_id, query_data):
        """获取分配策略列表"""
        from app.extensions import db
        from app.models.warehouse import StockAllocationPolicy
        from sqlalchemy import select
        
        query = select(StockAllocationPolicy).where(
            StockAllocationPolicy.virtual_warehouse_id == virtual_warehouse_id
        )
        
        # 分页
        from sqlalchemy import func
        total = db.session.execute(select(func.count()).select_from(query.subquery())).scalar()
        offset = (query_data['page'] - 1) * query_data['per_page']
        query = query.offset(offset).limit(query_data['per_page'])
        
        policies = db.session.execute(query).scalars().all()
        
        return {
            'items': policies,
            'total': total,
            'page': query_data['page'],
            'per_page': query_data['per_page']
        }
    
    @virtual_bp.doc(summary='创建分配策略', description='为虚拟仓创建新的分配策略')
    @virtual_bp.input(StockAllocationPolicyCreateSchema, arg_name='data')
    @virtual_bp.output(StockAllocationPolicySchema, status_code=201)
    @permission_required('virtual:create')
    def post(self, virtual_warehouse_id, data):
        """创建分配策略"""
        user_id = get_jwt_identity()
        data['virtual_warehouse_id'] = virtual_warehouse_id
        policy = virtual_service.create_allocation_policy(data, user_id)
        return {'data': policy}


class AllocationPolicyItemAPI(MethodView):
    """单个分配策略API"""
    decorators = [virtual_bp.auth_required(auth)]
    
    @virtual_bp.doc(summary='获取分配策略详情', description='根据ID获取分配策略详细信息')
    @virtual_bp.output(StockAllocationPolicySchema)
    @permission_required('virtual:view')
    def get(self, policy_id):
        """获取分配策略详情"""
        from app.extensions import db
        from app.models.warehouse import StockAllocationPolicy
        from app.errors import BusinessError
        
        policy = db.session.get(StockAllocationPolicy, policy_id)
        if not policy:
            raise BusinessError(f'分配策略 {policy_id} 不存在', code=404)
        return {'data': policy}
    
    @virtual_bp.doc(summary='更新分配策略', description='更新分配策略信息')
    @virtual_bp.input(StockAllocationPolicyUpdateSchema, arg_name='data')
    @virtual_bp.output(StockAllocationPolicySchema)
    @permission_required('virtual:update')
    def put(self, policy_id, data):
        """更新分配策略"""
        policy = virtual_service.update_allocation_policy(policy_id, data)
        return {'data': policy}
    
    @virtual_bp.doc(summary='删除分配策略', description='删除分配策略')
    @virtual_bp.output({})
    @permission_required('virtual:delete')
    def delete(self, policy_id):
        """删除分配策略"""
        virtual_service.delete_allocation_policy(policy_id)
        return {'data': None}


class ProductGroupListAPI(MethodView):
    """SKU分组列表API"""
    decorators = [virtual_bp.auth_required(auth)]
    
    @virtual_bp.doc(summary='获取SKU分组列表', description='获取SKU分组列表')
    @virtual_bp.input(PaginationQuerySchema, location='query', arg_name='query_data')
    @virtual_bp.output(ProductGroupPaginationSchema)
    @permission_required('virtual:view')
    def get(self, query_data):
        """获取SKU分组列表"""
        from app.extensions import db
        from app.models.warehouse import WarehouseProductGroup
        from sqlalchemy import select
        
        query = select(WarehouseProductGroup)
        
        if query_data.get('q'):
            query = query.where(
                WarehouseProductGroup.code.ilike(f'%{query_data["q"]}%') |
                WarehouseProductGroup.name.ilike(f'%{query_data["q"]}%')
            )
        
        # 分页
        from sqlalchemy import func
        total = db.session.execute(select(func.count()).select_from(query.subquery())).scalar()
        offset = (query_data['page'] - 1) * query_data['per_page']
        query = query.offset(offset).limit(query_data['per_page'])
        
        groups = db.session.execute(query).scalars().all()
        
        return {
            'items': groups,
            'total': total,
            'page': query_data['page'],
            'per_page': query_data['per_page']
        }
    
    @virtual_bp.doc(summary='创建SKU分组', description='创建新的SKU分组')
    @virtual_bp.input(WarehouseProductGroupCreateSchema, arg_name='data')
    @virtual_bp.output(WarehouseProductGroupSchema, status_code=201)
    @permission_required('virtual:create')
    def post(self, data):
        """创建SKU分组"""
        from app.extensions import db
        from app.models.warehouse import WarehouseProductGroup
        from app.errors import BusinessError
        from flask_jwt_extended import get_jwt_identity
        
        # 检查编码是否重复
        existing = db.session.execute(
            select(WarehouseProductGroup).where(WarehouseProductGroup.code == data['code'])
        ).scalar_one_or_none()
        
        if existing:
            raise BusinessError(f'SKU分组编码 {data["code"]} 已存在', code=400)
        
        # 创建分组
        group = WarehouseProductGroup(
            code=data['code'],
            name=data['name'],
            note=data.get('note'),
            created_by=get_jwt_identity()
        )
        
        db.session.add(group)
        db.session.commit()
        
        return {'data': group}


class ProductGroupItemAPI(MethodView):
    """单个SKU分组API"""
    decorators = [virtual_bp.auth_required(auth)]
    
    @virtual_bp.doc(summary='获取SKU分组详情', description='根据ID获取SKU分组详细信息')
    @virtual_bp.output(WarehouseProductGroupSchema)
    @permission_required('virtual:view')
    def get(self, group_id):
        """获取SKU分组详情"""
        from app.extensions import db
        from app.models.warehouse import WarehouseProductGroup
        from app.errors import BusinessError
        
        group = db.session.get(WarehouseProductGroup, group_id)
        if not group:
            raise BusinessError(f'SKU分组 {group_id} 不存在', code=404)
        return {'data': group}
    
    @virtual_bp.doc(summary='更新SKU分组', description='更新SKU分组信息')
    @virtual_bp.input(WarehouseProductGroupCreateSchema, arg_name='data')
    @virtual_bp.output(WarehouseProductGroupSchema)
    @permission_required('virtual:update')
    def put(self, group_id, data):
        """更新SKU分组"""
        from app.extensions import db
        from app.models.warehouse import WarehouseProductGroup
        from app.errors import BusinessError
        
        group = db.session.get(WarehouseProductGroup, group_id)
        if not group:
            raise BusinessError(f'SKU分组 {group_id} 不存在', code=404)
        
        # 更新字段
        for key, value in data.items():
            if hasattr(group, key) and value is not None:
                setattr(group, key, value)
        
        db.session.commit()
        return {'data': group}
    
    @virtual_bp.doc(summary='删除SKU分组', description='删除SKU分组')
    @virtual_bp.output({})
    @permission_required('virtual:delete')
    def delete(self, group_id):
        """删除SKU分组"""
        from app.extensions import db
        from app.models.warehouse import WarehouseProductGroup
        from app.errors import BusinessError
        
        group = db.session.get(WarehouseProductGroup, group_id)
        if not group:
            raise BusinessError(f'SKU分组 {group_id} 不存在', code=404)
        
        db.session.delete(group)
        db.session.commit()
        return {'data': None}


class ProductGroupItemListAPI(MethodView):
    """SKU分组明细列表API"""
    decorators = [virtual_bp.auth_required(auth)]
    
    @virtual_bp.doc(summary='获取分组SKU列表', description='获取指定分组内的SKU列表')
    @virtual_bp.input(PaginationQuerySchema, location='query', arg_name='query_data')
    @virtual_bp.output({'items': {'type': 'array', 'items': {'type': 'object'}}})
    @permission_required('virtual:view')
    def get(self, group_id, query_data):
        """获取分组SKU列表"""
        from app.extensions import db
        from app.models.warehouse import WarehouseProductGroupItem
        from sqlalchemy import select
        
        query = select(WarehouseProductGroupItem).where(
            WarehouseProductGroupItem.group_id == group_id
        )
        
        # 分页
        from sqlalchemy import func
        total = db.session.execute(select(func.count()).select_from(query.subquery())).scalar()
        offset = (query_data['page'] - 1) * query_data['per_page']
        query = query.offset(offset).limit(query_data['per_page'])
        
        items = db.session.execute(query).scalars().all()
        
        return {
            'items': items,
            'total': total,
            'page': query_data['page'],
            'per_page': query_data['per_page']
        }
    
    @virtual_bp.doc(summary='添加SKU到分组', description='添加SKU到指定分组')
    @virtual_bp.input(WarehouseProductGroupItemCreateSchema, arg_name='data')
    @virtual_bp.output(WarehouseProductGroupItemSchema, status_code=201)
    @permission_required('virtual:update')
    def post(self, group_id, data):
        """添加SKU到分组"""
        from app.extensions import db
        from app.models.warehouse import WarehouseProductGroupItem
        from app.errors import BusinessError
        
        # 检查是否已存在
        existing = db.session.execute(
            select(WarehouseProductGroupItem).where(
                WarehouseProductGroupItem.group_id == group_id,
                WarehouseProductGroupItem.sku == data['sku']
            )
        ).scalar_one_or_none()
        
        if existing:
            raise BusinessError(f'SKU {data["sku"]} 已在分组中', code=400)
        
        # 添加SKU到分组
        item = WarehouseProductGroupItem(
            group_id=group_id,
            sku=data['sku']
        )
        
        db.session.add(item)
        db.session.commit()
        
        return {'data': item}


class ProductGroupItemRemoveAPI(MethodView):
    """移除分组SKU API"""
    decorators = [virtual_bp.auth_required(auth)]
    
    @virtual_bp.doc(summary='从分组移除SKU', description='从指定分组中移除SKU')
    @virtual_bp.output({})
    @permission_required('virtual:update')
    def delete(self, group_id, sku):
        """从分组移除SKU"""
        from app.extensions import db
        from app.models.warehouse import WarehouseProductGroupItem
        from sqlalchemy import delete
        
        # 删除SKU
        db.session.execute(
            delete(WarehouseProductGroupItem).where(
                WarehouseProductGroupItem.group_id == group_id,
                WarehouseProductGroupItem.sku == sku
            )
        )
        db.session.commit()
        
        return {'data': None}


# 注册路由
virtual_bp.add_url_rule('', view_func=VirtualWarehouseListAPI.as_view('virtual_warehouse_list'))
virtual_bp.add_url_rule('/<int:virtual_warehouse_id>/stock', view_func=VirtualStockAPI.as_view('virtual_stock'))
virtual_bp.add_url_rule('/<int:virtual_warehouse_id>/policies', view_func=AllocationPolicyListAPI.as_view('allocation_policy_list'))
virtual_bp.add_url_rule('/policies/<int:policy_id>', view_func=AllocationPolicyItemAPI.as_view('allocation_policy_item'))
virtual_bp.add_url_rule('/product-groups', view_func=ProductGroupListAPI.as_view('product_group_list'))
virtual_bp.add_url_rule('/product-groups/<int:group_id>', view_func=ProductGroupItemAPI.as_view('product_group_item'))
virtual_bp.add_url_rule('/product-groups/<int:group_id>/items', view_func=ProductGroupItemListAPI.as_view('product_group_item_list'))
virtual_bp.add_url_rule('/product-groups/<int:group_id>/items/<string:sku>', view_func=ProductGroupItemRemoveAPI.as_view('product_group_item_remove'))
