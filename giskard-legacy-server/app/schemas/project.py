from datetime import datetime

from app.schemas.user import UserMinimalSchema
from typing import Optional, List

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: str = None
    description: str = None


# All properties stored in DB
class ProjectSchema(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str]
    created_on: datetime
    owner_id: int
    owner_details: UserMinimalSchema
    guest_list: List[UserMinimalSchema]

    class Config:
        orm_mode = True
