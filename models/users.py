from core.database import Base
from sqlalchemy import (Column, Integer, String, Boolean, DateTime)
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    #pk 
    id = Column(Integer, primary_key=True, index=True)

    #relationships
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    
    
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="customer")
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
