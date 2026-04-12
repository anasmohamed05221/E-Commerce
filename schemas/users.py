from pydantic import BaseModel
from models.enums import UserRole
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