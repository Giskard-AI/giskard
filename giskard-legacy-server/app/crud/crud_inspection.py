from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Dataset
from app.models.inspection import Inspection
from app.schemas.project_file import ProjectFileCreateSchema, InspectionCreateSchema


class CRUDInspection(CRUDBase[Inspection, InspectionCreateSchema, InspectionCreateSchema]):
    def create(
        self, db: Session, obj_in: InspectionCreateSchema,model_id, dataset_id,
    ) -> Inspection:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data,model_id=model_id, dataset_id=dataset_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj



inspection = CRUDInspection(Inspection)
