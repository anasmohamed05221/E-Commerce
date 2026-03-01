from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


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