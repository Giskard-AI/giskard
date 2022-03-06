from app.core.config import settings
from .role import RoleSchema
from typing import Optional

from pydantic import BaseModel


# Properties to receive via API on creation
from app.core.base_model import CaseInsensitiveEmailStr


class UserCreate(BaseModel):
    user_id: str
    email: CaseInsensitiveEmailStr
    password: str
    display_name: Optional[str] = None
    role_id: Optional[int] = settings.UserRole.AI_CREATOR.value


# Properties to receive via API on update
class UserUpdate(BaseModel):
    password: Optional[str] = None
    display_name: Optional[str] = None
    role_id: Optional[int] = None
    email: Optional[CaseInsensitiveEmailStr] = None
    is_active: Optional[bool] = None


class UserMinimalSchema(BaseModel):
    user_id: str
    display_name: Optional[str] = None

    class Config:
        orm_mode = True


class UserSchema(UserMinimalSchema):
    id: int
    email: str
    is_active: bool
    role: RoleSchema


# Additional properties stored in DB
class UserFullSchema(UserSchema):
    hashed_password: str
