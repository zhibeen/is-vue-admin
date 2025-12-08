from typing import Optional
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

class ProductBusinessRule(db.Model):
    __tablename__ = 'product_business_rules'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 关联字典 product_business_type 的 value，如 'vehicle', 'general'
    business_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="业务类型代码")
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="规则名称")
    
    # SKU/SPU 生成策略配置
    generate_strategy: Mapped[str] = mapped_column(String(50), default='general', comment="编码生成策略: vehicle/general/custom")
    sku_prefix: Mapped[Optional[str]] = mapped_column(String(10), comment="SKU前缀")
    
    # 业务流程配置
    requires_audit: Mapped[bool] = mapped_column(Boolean, default=False, comment="创建产品是否需要审核")
    
    # 扩展配置
    config: Mapped[Optional[dict]] = mapped_column(JSONB, comment="其他扩展配置")

    def __repr__(self):
        return f"<ProductBusinessRule {self.business_type}>"

