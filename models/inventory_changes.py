from core.database import Base
from sqlalchemy import (Column, Integer, ForeignKey, Enum)
from sqlalchemy.orm import relationship
from .mixins import CreatedAtMixin
from .enums import InventoryChangeReason

class InventoryChange(Base, CreatedAtMixin):
    __tablename__ = "inventory_changes"

    #pk
    id = Column(Integer, primary_key=True, index=True)
    
    #fk
    product_id = Column(Integer, ForeignKey("products.id"))
    
    #relationships
    product = relationship("Product", back_populates="inventory_changes")


    change_amount = Column(Integer)
    reason = Column(Enum(InventoryChangeReason, values_callable=lambda obj: [e.value for e in obj], name="reason"))
