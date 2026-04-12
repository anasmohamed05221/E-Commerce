from core.database import Base
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Enum)
from sqlalchemy.orm import relationship
from .enums import UserRole

class User(Base):
    __tablename__ = "users"

    #pk 
    id = Column(Integer, primary_key=True, index=True)

    #relationships
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user", passive_deletes=True)
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    addresses = relationship("Address", back_populates="user", passive_deletes=True)
    
    email = Column(String(255), unique=True, nullable=False)
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
    password_change_token = Column(String(255), nullable=True)
    password_change_expires_at = Column(DateTime(timezone=True), nullable=True)
    # Password reset fields
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
