from sqlalchemy.sql import func
from sqlalchemy import Column, DateTime


class CreatedAtMixin:
    created_at = Column(DateTime(timezone=True), default=func.now())
class UpdatedAtMixin:
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
