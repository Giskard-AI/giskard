from datetime import datetime
from pydantic import BaseModel


class ProjectFileCreateSchema(BaseModel):
    file_name: str
    location: str


class ProjectModelCreateSchema(ProjectFileCreateSchema):
    file_name: str
    location: str
    python_version: str
    requirements_file_location: str


class ProjectFileSchema(BaseModel):
    id: int
    name: str
    size: int
    creation_date: datetime
    project_id: int


class ProjectFileMinimalSchema(BaseModel):
    id: int
    file_name: str

    class Config:
	    orm_mode=True


class ProjectModelFileSchema(ProjectFileSchema):
    python_version: str
