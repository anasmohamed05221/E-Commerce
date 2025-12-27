from core.database import Base
from sqlalchemy import (Column, Integer, ForeignKey)
from sqlalchemy.orm import relationship
from .mixins import CreatedAtMixin

class CartItem(Base, CreatedAtMixin):
    __tablename__ = "cart_items"

    #pk
    id = Column(Integer, primary_key=True, index=True)

    #fk
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    #relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

    quantity = Column(Integer)