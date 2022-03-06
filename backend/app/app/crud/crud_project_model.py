from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import ProjectModel
from app.schemas.project_file import ProjectModelCreateSchema


class CRUDProjectModel(CRUDBase[ProjectModel, ProjectModelCreateSchema, ProjectModelCreateSchema]):
    def create(
        self, db: Session, obj_in: ProjectModelCreateSchema, project_id: int, owner_id: int
    ) -> ProjectModel:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id, project_id=project_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_all_by_project(
        self, db: Session, *, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[ProjectModel]:
        return (
            db.query(self.model)
            .filter(ProjectModel.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


project_model = CRUDProjectModel(ProjectModel)
