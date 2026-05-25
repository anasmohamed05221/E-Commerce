from core.database import Base
from sqlalchemy import (Column, Integer, String, ForeignKey, Boolean)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .mixins import CreatedAtMixin

class Address(Base, CreatedAtMixin):
    __tablename__="addresses"

    #pk
    id = Column(Integer, primary_key=True)

    #fk
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    #relationships
    tenant = relationship("Tenant", back_populates="addresses")
    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="address")

    label = Column(String(50))
    street = Column(String(255), nullable=False)
    city = Column(String(100), index=True, nullable=False)
    state = Column(String(100))
    country = Column(String(100), index=True, nullable=False)
    postal_code = Column(String(20), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)