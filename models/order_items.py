from core.database import Base
from sqlalchemy import (Column, Integer, ForeignKey, Numeric, CheckConstraint)
from sqlalchemy.orm import relationship

class OrderItem(Base):
    __tablename__ = "order_items"

    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_item_quantity_positive"),
        CheckConstraint("price_at_time >= 0", name="ck_orderItem_price_non_negative"),
        CheckConstraint("subtotal >= 0", name="ck_orderItem_subtotal_non_negative"),
    )

    #pk
    id = Column(Integer, primary_key=True)

    #fk
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    #relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


    price_at_time = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)