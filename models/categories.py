from core.database import Base
from sqlalchemy.sql import func
from sqlalchemy import (Column, Integer, String, DateTime)
from sqlalchemy.orm import relationship
from .mixins import CreatedAtMixin

class Category(Base, CreatedAtMixin):
    __tablename__ = "categories"

    #pk
    id = Column(Integer, primary_key=True, index=True)

    #relationships
    products = relationship("Product", back_populates="category")

    name = Column(String)
    description = Column(String)