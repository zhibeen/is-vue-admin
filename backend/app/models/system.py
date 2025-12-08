from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class SysDict(db.Model):
    __tablename__ = 'sys_dictionaries'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # e.g. 'product_business_type'
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(50), comment="业务分类") # e.g. 'finance', 'purchase'
    description: Mapped[Optional[str]] = mapped_column(String(200))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False) # True=不可删除
    
    # 存储预设的值选项，用于前端渲染 Select
    # 格式示例: [{"label": "选项A", "value": "a"}, {"label": "选项B", "value": "b"}]
    value_options: Mapped[Optional[list]] = mapped_column(JSONB)

    def __repr__(self):
        return f"<SysDict {self.code}>"


