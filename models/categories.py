from core.database import Base
from sqlalchemy import (Column, Integer, String, ForeignKey, UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .mixins import CreatedAtMixin

class Category(Base, CreatedAtMixin):
    __tablename__ = "categories"

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_category_tenant_name"),
    )

    #pk
    id = Column(Integer, primary_key=True)

    #fk
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    #relationships
    tenant = relationship("Tenant", back_populates="categories")
    products = relationship("Product", back_populates="category")

    name = Column(String, nullable=False)
    description = Column(String)