from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=100)

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CartProductOut(BaseModel):
    id: int
    name: str
    price: Decimal
    image_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class CartItemOut(BaseModel):
    id: int
    product: CartProductOut
    quantity: int
    
    model_config = {
        "from_attributes": True
    }

class CartOut(BaseModel):
    cart_items: list[CartItemOut]
    total_price: Decimal