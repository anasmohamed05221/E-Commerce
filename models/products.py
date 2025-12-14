from core.database import Base
from sqlalchemy.sql import func
from sqlalchemy import (Column, Integer, String, ForeignKey, Numeric, DateTime)
from sqlalchemy.orm import relationship
from .mixins import CreatedAtMixin, UpdatedAtMixin

class Product(Base, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "products"

    #pk
    id = Column(Integer, primary_key=True, index=True)

    #fk
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    #relationships
    order_items = relationship("OrderItem", back_populates="product")
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    inventory_changes = relationship("InventoryChange", back_populates="product")

    name = Column(String)
    description = Column(String)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String)
    stock = Column(Integer)
    rating = Column(Integer)