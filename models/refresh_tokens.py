from core.database import Base
from sqlalchemy import Column, Boolean, DateTime, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from models.mixins import CreatedAtMixin

class RefreshToken(Base, CreatedAtMixin):
    """
    Stores refresh tokens for user authentication.
    
    Refresh tokens are long-lived (7 days) and allow users to get new
    access tokens without re-logging in. Tokens are hashed for security.
    """
    __tablename__ = "refresh_tokens"

    #pk
    id = Column(Integer, primary_key=True, index=True)

    #fk
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    #relationships
    user = relationship("User", back_populates="refresh_tokens")

    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
