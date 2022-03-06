from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.project import ProjectCreate
from app.tests.utils.utils import random_lower_string


def create_random_project(db: Session, owner_id: int = 1) -> models.Project:
    name = random_lower_string()
    description = random_lower_string()
    project_in = ProjectCreate(name=name, description=description)
    return crud.project.create(db, project_in, owner_id)
