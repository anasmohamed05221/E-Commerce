from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime

# List products response
class ProductListItemOut(BaseModel):
    id: int
    name: str
    price: Decimal
    stock: int
    image_url: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    category_id: int

    model_config = {
    "from_attributes": True
    }
