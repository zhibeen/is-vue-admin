import pytest
from app.services.code_builder import CodeBuilderService
from app.models.product import Category, AttributeDefinition, CategoryAttribute, ProductVehicleBrand
from app.extensions import db

class TestCodeBuilder:
    
    @pytest.fixture
    def setup_data(self, app):
        """准备测试数据"""
        with app.app_context():
            # 1. 属性定义
            attr_pos = AttributeDefinition(key_name='position', label='Position', data_type='select', code_weight=10, include_in_code=True, options=[{'label': 'Left', 'code': 'L'}])
            attr_col = AttributeDefinition(key_name='color', label='Color', data_type='select', code_weight=30, include_in_code=True, options=[{'label': 'Black', 'code': 'BK'}])
            db.session.add_all([attr_pos, attr_col])
            db.session.flush()
            
            # 2. 分类结构
            # 父分类: Auto Parts (定义了 SPU 模板)
            parent = Category(
                name='Auto Parts', 
                code='100', 
                abbreviation='AP', 
                spu_config={"template": "{cat}-{brand}-{model}"}
            )
            db.session.add(parent)
            db.session.flush()
            
            # 子分类 1: Headlight (继承父类模板，正常显示颜色)
            cat_hl = Category(name='Headlight', code='101', abbreviation='HL', parent_id=parent.id)
            db.session.add(cat_hl)
            
            # 子分类 2: Foglight (继承父类模板，但覆盖颜色属性为不进编码)
            cat_fl = Category(name='Foglight', code='102', abbreviation='FL', parent_id=parent.id)
            db.session.add(cat_fl)
            db.session.flush()
            
            # 3. 绑定属性
            # HL: 正常绑定
            db.session.add(CategoryAttribute(category_id=cat_hl.id, attribute_id=attr_pos.id))
            db.session.add(CategoryAttribute(category_id=cat_hl.id, attribute_id=attr_col.id))
            
            # FL: 覆盖绑定 (include_in_code=False)
            db.session.add(CategoryAttribute(category_id=cat_fl.id, attribute_id=attr_pos.id))
            db.session.add(CategoryAttribute(
                category_id=cat_fl.id, 
                attribute_id=attr_col.id,
                include_in_code=False # <--- 关键测试点
            ))
            
            db.session.commit()
            
            yield {
                'hl_id': cat_hl.id,
                'fl_id': cat_fl.id,
                'parent_id': parent.id
            }

    def test_spu_inheritance(self, app, setup_data):
        """测试 SPU 模板继承"""
        with app.app_context():
            metadata = {"brand": "BMW", "model": "X5"}
            
            # 1. 子分类 HL 应该继承父类的模板 "{cat}-{brand}-{model}"
            # 这里的 cat 应该是子类的 abbreviation 'HL'
            spu_code = CodeBuilderService.generate_spu_code(setup_data['hl_id'], metadata)
            assert spu_code == "HL-BMW-X5"

    def test_sku_override(self, app, setup_data):
        """测试 SKU 属性覆盖 (include_in_code)"""
        with app.app_context():
            spu_code = "TEST-SPU"
            specs = {"position": "Left", "color": "Black"}
            
            # 1. Headlight: 正常包含所有属性
            # 排序权重: Position(10) -> Color(30)
            # 预期: SPU-L-BK
            sku_hl = CodeBuilderService.generate_sku_feature_code(spu_code, specs, category_id=setup_data['hl_id'])
            assert sku_hl == "TEST-SPU-L-BK"
            
            # 2. Foglight: 颜色被强制关闭
            # 预期: SPU-L (不包含 BK)
            sku_fl = CodeBuilderService.generate_sku_feature_code(spu_code, specs, category_id=setup_data['fl_id'])
            assert sku_fl == "TEST-SPU-L"
            assert "BK" not in sku_fl

