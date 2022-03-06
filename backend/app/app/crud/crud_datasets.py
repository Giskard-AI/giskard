from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Dataset
from app.schemas.project_file import ProjectFileCreateSchema


class CRUDDataset(CRUDBase[Dataset, ProjectFileCreateSchema, ProjectFileCreateSchema]):
    def create(
        self, db: Session, obj_in: ProjectFileCreateSchema, project_id: int, owner_id: int
    ) -> Dataset:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id, project_id=project_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_all_by_project(
        self, db: Session, *, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[Dataset]:
        return (
            db.query(self.model)
            .filter(Dataset.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


dataset = CRUDDataset(Dataset)
