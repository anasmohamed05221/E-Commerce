from core.database import Base
from sqlalchemy import (Column, Integer, ForeignKey, Numeric)
from sqlalchemy.orm import relationship

class OrderItem(Base):
    __tablename__ = "order_items"

    #pk
    id = Column(Integer, primary_key=True, index=True)

    #fk
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    #relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


    price_at_time = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)