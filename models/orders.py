from core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import (Column, Integer, ForeignKey ,Numeric, Enum)
from .mixins import CreatedAtMixin, UpdatedAtMixin

class Order(Base, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "orders"

    #pk
    id = Column(Integer, primary_key=True, index=True)

    #fk
    user_id = Column(Integer, ForeignKey("users.id"))

    #relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum("pending", "confirmed", "completed", "cancelled", name="order_status"), default="pending")
    

