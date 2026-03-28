from pydantic import BaseModel
from models.enums import OrderStatus
from decimal import Decimal
from datetime import datetime
from typing import Optional


class OrderProductOut(BaseModel):
    id: int
    name: str
    price: Decimal
    image_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class OrderItemOut(BaseModel):
    id: int
    product: OrderProductOut
    price_at_time: Decimal
    quantity: int
    subtotal: Decimal

    model_config = {
        'from_attributes': True
    }
    

class OrderOut(BaseModel):
    id: int
    total_amount: Decimal
    status: OrderStatus
    items: list[OrderItemOut]
    created_at: datetime
    updated_at: datetime

    model_config = {
        'from_attributes': True
    }


class OrderSummaryOut(BaseModel):
    id: int
    total_amount: Decimal
    status: OrderStatus
    created_at: datetime

    model_config = {
        'from_attributes': True
    }