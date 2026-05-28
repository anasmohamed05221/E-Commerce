from pydantic import BaseModel, Field, EmailStr, field_validator
from models.enums import PlanTier
from utils.validators import validate_password
from uuid import UUID
from datetime import datetime

class TenantRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=3, max_length=50, pattern=r"^[a-z0-9][a-z0-9-]{2,49}$")
    email: EmailStr
    password: str
    plan: PlanTier = PlanTier.FREE

    @field_validator('password')
    @classmethod
    def validate_password(cls, value):
        return validate_password(value)

class TenantOut(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: PlanTier
    is_active: bool
    created_at: datetime
    
    model_config = {
        'from_attributes': True
    }

class TenantRegisterOut(TenantOut):
    api_key: str
    message: str