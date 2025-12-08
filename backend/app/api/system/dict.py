from apiflask import APIBlueprint, Schema, abort
from apiflask.fields import String, Integer, Boolean, List, Dict as DictField
from apiflask.views import MethodView
from sqlalchemy import select
from app.extensions import db
from app.models.system import SysDict
from app.security import auth

# Blueprint
system_bp = APIBlueprint('system', __name__, url_prefix='/system', tag='System')

# Schemas
class DictSchema(Schema):
    id = Integer(dump_only=True)
    code = String(required=True)
    name = String(required=True)
    category = String(allow_none=True)
    description = String(allow_none=True)
    is_system = Boolean(dump_only=True)
    value_options = List(DictField(), allow_none=True)

class DictItemSchema(Schema):
    id = Integer(dump_only=True)
    dict_id = Integer(dump_only=True)
    value = String(required=True)
    label = String(required=True)
    meta_data = DictField()
    sort_order = Integer()
    is_active = Boolean()

# --- Dict APIs ---

class DictListAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取字典列表')
    @system_bp.output(DictSchema(many=True))
    def get(self):
        """List all dictionaries"""
        dicts = db.session.scalars(select(SysDict).order_by(SysDict.code)).all()
        return {'data': dicts}

    @system_bp.doc(summary='创建字典')
    @system_bp.input(DictSchema, arg_name='data')
    @system_bp.output(DictSchema)
    def post(self, data):
        """Create a dictionary"""
        if db.session.scalar(select(SysDict).where(SysDict.code == data['code'])):
            abort(400, 'Dictionary code already exists')
        
        d = SysDict(**data)
        db.session.add(d)
        db.session.commit()
        return {'data': d}

class DictDetailAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]

    @system_bp.doc(summary='更新字典')
    @system_bp.input(DictSchema(partial=True), arg_name='data')
    @system_bp.output(DictSchema)
    def put(self, dict_id, data):
        d = db.session.get(SysDict, dict_id)
        if not d:
            abort(404)
        if d.is_system:
            # System dicts might have restricted editing
            pass
            
        for k, v in data.items():
            setattr(d, k, v)
        db.session.commit()
        return {'data': d}

    @system_bp.doc(summary='删除字典')
    def delete(self, dict_id):
        d = db.session.get(SysDict, dict_id)
        if not d:
            abort(404)
        # Allow deleting system dicts for flexibility, or could use a query param to force
        # if d.is_system:
        #     abort(400, 'Cannot delete system dictionary')
            
        db.session.delete(d)
        db.session.commit()
        return None

# --- Dict Item APIs ---

class DictItemListAPI(MethodView):
    decorators = [system_bp.auth_required(auth)]
    
    @system_bp.doc(summary='获取字典项列表')
    @system_bp.output(DictItemSchema(many=True))
    def get(self, dict_code):
        """Get items for a specific dictionary code"""
        # Find dict by code first
        d = db.session.scalar(select(SysDict).where(SysDict.code == dict_code))
        if not d:
            # Return empty if not found, or 404? Empty is safer for frontend
            return {'data': []}

        # Fallback: 如果没有物理项，尝试返回 value_options 中的预设值
        if d.value_options and isinstance(d.value_options, list):
            virtual_items = []
            try:
                for idx, opt in enumerate(d.value_options):
                    if isinstance(opt, dict) and 'value' in opt and 'label' in opt:
                        virtual_items.append({
                            'id': -1 * (idx + 1), # 负数 ID 表示虚拟项
                            'dict_id': d.id,
                            'value': str(opt['value']),
                            'label': str(opt['label']),
                            'sort_order': (idx + 1) * 10,
                            'is_active': True,
                            'meta_data': {}
                        })
            except Exception:
                pass
            
            if virtual_items:
                return {'data': virtual_items}

        return {'data': []}

# Register Routes
system_bp.add_url_rule('/dicts', view_func=DictListAPI.as_view('dict_list'))
system_bp.add_url_rule('/dicts/<int:dict_id>', view_func=DictDetailAPI.as_view('dict_detail'))
system_bp.add_url_rule('/dicts/<string:dict_code>/items', view_func=DictItemListAPI.as_view('dict_item_list_by_code'))

