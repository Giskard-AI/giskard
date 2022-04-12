from typing import Optional

from pydantic.main import BaseModel

from app.schemas import UserSchema


class AppConfig(BaseModel):
    plan_code: str
    plan_name: str
    seats_available: Optional[int]


class AppUserConfig(BaseModel):
    app: AppConfig
    user: UserSchema

    class Config:
        arbitrary_types_allowed = True
