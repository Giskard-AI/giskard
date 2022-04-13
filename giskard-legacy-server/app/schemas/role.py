from pydantic import BaseModel


class RoleSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
