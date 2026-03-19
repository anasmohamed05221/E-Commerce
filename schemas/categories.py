from pydantic import BaseModel

class CategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {
        "from_attributes": True
    }
