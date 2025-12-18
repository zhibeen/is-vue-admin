from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

class OverseasConsignee(db.Model):
    """
    境外收货人 (Consignee)
    """
    __tablename__ = "customs_overseas_consignees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment='收货人名称')
    address: Mapped[str] = mapped_column(String(500), nullable=True, comment='地址')
    contact_info: Mapped[str] = mapped_column(String(200), nullable=True, comment='联系方式')
    country: Mapped[str] = mapped_column(String(100), nullable=True, comment='国家/地区')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    
    def __repr__(self):
        return f"<OverseasConsignee {self.name}>"

