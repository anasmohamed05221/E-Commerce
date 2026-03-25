from pydantic import BaseModel, model_validator
from decimal import Decimal
from typing import Optional
from schemas.categories import CategoryOut
from datetime import datetime
from fastapi import Query

class ProductFilterParams(BaseModel):
    limit: int = Query(default=20, ge=1, le=100)
    offset: int = Query(default=0, ge=0)
    category_id: Optional[int] = Query(default=None)
    min_price: Optional[Decimal] = Query(default=None, ge=0)
    max_price: Optional[Decimal] = Query(default=None, ge=0)

    @model_validator(mode='after')
    def validate_price_range(self):
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price must be less than or equal to max_price")
        return self


# Product list item
class ProductListItemOut(BaseModel):
    id: int
    name: str
    price: Decimal
    stock: int
    image_url: Optional[str] = None
    rating: Optional[float] = None
    category_id: int

    model_config = {
        "from_attributes": True
    }


# Product List 
class ProductListOut(BaseModel):
    items: list[ProductListItemOut]
    limit: int
    offset: int
    total: int


class ProductDetailOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int
    image_url: Optional[str] = None
    rating: Optional[float] = None
    category: CategoryOut
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }