from pydantic import BaseModel, field_validator, model_validator, Field
from models.enums import UserRole
from utils.validators import validate_phone
from typing import Optional


class PasswordChangeToken(BaseModel):
    token: str
    

class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = Field(min_length=1, max_length=50, default=None)
    last_name: Optional[str] = Field(min_length=1, max_length=50, default=None)
    phone_number: Optional[str] = None

    @model_validator(mode="after")
    def not_all_fields_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, value):
        return validate_phone(value)


class AdminUserOut(UserOut):
    role: UserRole
    is_active: bool
    is_verified: bool


class UserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserListOut(BaseModel):
    items: list[AdminUserOut]
    limit: int
    offset: int
    total: int