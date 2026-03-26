from pydantic import BaseModel
from decimal import Decimal
from enum import Enum
from datetime import datetime
from typing import Optional

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


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