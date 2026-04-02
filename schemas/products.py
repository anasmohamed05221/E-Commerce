from pydantic import BaseModel, Field, model_validator
from decimal import Decimal
from typing import Optional
from schemas.categories import CategoryOut
from datetime import datetime
from fastapi import Query, HTTPException, status


class ProductFilterParams:
    def __init__(
        self,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        category_id: Optional[int] = Query(default=None),
        min_price: Optional[Decimal] = Query(default=None, ge=0),
        max_price: Optional[Decimal] = Query(default=None, ge=0),
    ):
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="min_price must be less than or equal to max_price"
            )
        self.limit = limit
        self.offset = offset
        self.category_id = category_id
        self.min_price = min_price
        self.max_price = max_price


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


class ProductCreate(BaseModel):
    name: str
    price: Decimal = Field(ge=0.00)
    stock: int = Field(ge=0)
    category_id: int
    description: Optional[str] = None
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0.00)
    stock: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    
    @model_validator(mode="after")
    def not_all_fields_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self