from typing import Optional
from sqlalchemy import String, Integer, Text, Boolean, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

class CustomsProduct(db.Model):
    """
    报关商品/品类库 (Customs Product Library)
    用于管理标准化的报关信息，如 HS Code、申报要素模板等。
    """
    __tablename__ = "customs_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 核心信息
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment='报关通用名称')
    hs_code: Mapped[str] = mapped_column(String(50), nullable=False, comment='海关编码')
    
    # 申报信息
    rebate_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 4), comment='退税率')
    unit: Mapped[Optional[str]] = mapped_column(String(20), comment='申报单位')
    elements: Mapped[Optional[str]] = mapped_column(Text, comment='申报要素模板')
    
    # 其他
    description: Mapped[Optional[str]] = mapped_column(Text, comment='备注说明')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    
    def __repr__(self):
        return f"<CustomsProduct {self.name}>"

