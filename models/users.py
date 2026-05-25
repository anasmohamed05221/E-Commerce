from core.database import Base
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Index, text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .enums import UserRole

class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        Index("uq_user_tenant_email", "tenant_id", text("lower(email)"), unique=True),
    )

    #pk 
    id = Column(Integer, primary_key=True)

    #fk
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    #relationships
    tenant = relationship("Tenant", back_populates="users")
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user", passive_deletes=True)
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    addresses = relationship("Address", back_populates="user", passive_deletes=True)
    
    email = Column(String(255), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    """is_active = False means:
    - User cannot authenticate
    - User is treated as deleted / deactivated
    - User is excluded from all business logic
    """
    role = Column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj], name="userrole"), default=UserRole.CUSTOMER, nullable=False)
    phone_number = Column(String)
    # Email verification fields
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_code = Column(String(6), nullable=True)
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    # Password change fields
    pending_password_hash = Column(String(255), nullable=True)
    password_change_token = Column(String(255), nullable=True, unique=True)
    password_change_expires_at = Column(DateTime(timezone=True), nullable=True)
    # Password reset fields
    password_reset_token = Column(String(255), nullable=True, unique=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
