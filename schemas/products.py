from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from schemas.categories import CategoryOut
from datetime import datetime

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