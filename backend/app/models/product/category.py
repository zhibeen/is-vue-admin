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
    
    # 覆盖全局配置: 是否参与编码 (None=使用全局, True=强制参与, False=强制不参与)
    include_in_code: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # 覆盖全局选项: 如果不为None，则完全替代 AttributeDefinition.options
    options: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, comment="Override global options if set")
    
    # 覆盖分组: 如果不为None，则覆盖 AttributeDefinition.group_name
    group_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="Override attribute group")

    # 新增: 属性作用域 (spu=公共属性, sku=变体属性)
    attribute_scope: Mapped[Optional[str]] = mapped_column(String(10), default='spu', comment="属性作用域: spu/sku")
    
    # 新增: 是否允许自定义值 (覆盖全局配置)
    allow_custom: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, comment="Override allow_custom")

    # Relationships
    attribute_definition: Mapped["AttributeDefinition"] = relationship()

class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(100)) # 英文名称
    code: Mapped[Optional[str]] = mapped_column(String(10), unique=True) # SKU使用的类目码 (短码前缀)
    
    # 新增: 用于 SPU 特征码的缩写 (如 "HL")
    abbreviation: Mapped[Optional[str]] = mapped_column(String(10), comment="类目缩写,如 HL")
    
    # 业务类型: vehicle=汽配(默认), general=通用, electronics=电子
    business_type: Mapped[str] = mapped_column(String(20), default='vehicle', comment="业务线类型")

    # SPU 配置 (Schema Form 定义 & 模板)
    # { "template": "...", "fields": [...] }
    spu_config: Mapped[Optional[dict]] = mapped_column(JSONB, comment="SPU表单配置与生成模板")
    
    # Meta fields
    description: Mapped[Optional[str]] = mapped_column(String(500))
    icon: Mapped[Optional[str]] = mapped_column(String(50)) # Icon class or url
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    level: Mapped[Optional[int]] = mapped_column(Integer) # 缓存层级
    is_leaf: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(remote_side=[id], backref=db.backref("children", order_by="Category.sort_order"))
    
    # Many-to-Many with Metadata via Association Object
    attributes_association: Mapped[List["CategoryAttribute"]] = relationship(backref="category")
    
    # Products relationship (defined in Product model via string to avoid circular import)
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")

    @property
    def effective_spu_config(self):
        """
        获取生效的 SPU 配置（递归查找父级）
        """
        if self.spu_config:
            return self.spu_config
        
        if self.parent:
            return self.parent.effective_spu_config
            
        return None # 或者返回系统默认配置

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
    
    # 新增: 编码生成权重
    code_weight: Mapped[int] = mapped_column(Integer, default=99, comment="生成SKU特征码时的排序权重")
    include_in_code: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 新增: 属性分组 (例如: "技术参数", "包装信息")
    group_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="属性分组名称")
    
    # 新增: 英文名称
    name_en: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="英文名称")
    
    # 新增: 属性描述
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, comment="属性详细描述")

    # 新增: 是否允许自定义值 (仅对 select/radio 有效)
    allow_custom: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否允许输入自定义值")

    def __repr__(self):
        return f"<Attribute {self.key_name}>"

