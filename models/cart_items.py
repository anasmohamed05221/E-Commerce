from core.database import Base
from sqlalchemy import (Column, Integer, ForeignKey, UniqueConstraint, CheckConstraint)
from sqlalchemy.orm import relationship
from .mixins import CreatedAtMixin

class CartItem(Base, CreatedAtMixin):
    __tablename__ = "cart_items"

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
        CheckConstraint("quantity >= 1 AND quantity <= 100", name="ck_cart_quantity_range"),
    )

    #pk
    id = Column(Integer, primary_key=True, index=True)

    #fk
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    #relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

    quantity = Column(Integer, nullable=False, default=1)