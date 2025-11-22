from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class VehicleAux(db.Model):
    __tablename__ = "vehicle_aux"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vehicle_aux.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False) # Toyota, Camry, 2020
    code: Mapped[Optional[str]] = mapped_column(String(10)) # Brand Code: 01
    abbr: Mapped[Optional[str]] = mapped_column(String(10)) # Brand Abbr: BMW
    level_type: Mapped[Optional[str]] = mapped_column(String(20)) # brand, model, submodel
    full_path: Mapped[Optional[str]] = mapped_column(String(255)) # Cache: Toyota/Camry/2020
    
    # Relationships
    parent: Mapped[Optional["VehicleAux"]] = relationship(remote_side=[id], backref="children")
    
    # Fitments (Many-to-Many through ProductFitment)
    # Defined in ProductFitment to avoid circular imports here, or use string reference

    def __repr__(self):
        return f"<VehicleAux {self.name} ({self.level_type})>"
