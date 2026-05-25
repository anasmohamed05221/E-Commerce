from core.database import Base
from sqlalchemy import (Column, Integer, String, ForeignKey, Numeric, Float, CheckConstraint, UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .mixins import CreatedAtMixin, UpdatedAtMixin

class Product(Base, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_product_stock_non_negative"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_product_rating_range"),
        UniqueConstraint("tenant_id", "name", name="uq_product_tenant_name"),
    )

    #pk
    id = Column(Integer, primary_key=True)

    #fk
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), index=True, nullable=False)
    
    #relationships
    tenant = relationship("Tenant", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product", passive_deletes=True)
    inventory_changes = relationship("InventoryChange", back_populates="product")

    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Numeric(10, 2), nullable=False, index=True)
    image_url = Column(String)
    stock = Column(Integer, nullable=False)
    rating = Column(Float, nullable=True)
