from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional

class AddressCreate(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str
    label: Optional[str] = None
    state: Optional[str] = None
    is_default: bool = False


class AddressUpdate(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    label: Optional[str] = None
    state: Optional[str] = None
    is_default: Optional[bool] = None

    @model_validator(mode="after")
    def not_all_fields_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self
    

class AddressOut(BaseModel):
    id: int
    user_id: int
    street: str
    city: str
    country: str
    postal_code: str
    label: Optional[str] = None
    state: Optional[str] = None
    is_default: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }