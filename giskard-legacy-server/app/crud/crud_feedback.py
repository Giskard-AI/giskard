from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreateSchema


class CRUDFeedback(CRUDBase[Feedback, FeedbackCreateSchema, FeedbackCreateSchema]):
    def create(
        self, db: Session, obj_in: FeedbackCreateSchema, user_id: int
    ) -> Feedback:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_all_by_project(
        self, db: Session, *, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[Feedback]:
        return (
            db.query(self.model)
            .filter(Feedback.project_id == project_id, Feedback.model_id != None, Feedback.dataset_id != None)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_project_and_user(
        self, db: Session, *, project_id: int, user_id: int
    ) -> List[Feedback]:
        return (
            db.query(self.model)
            .filter(Feedback.project_id == project_id, Feedback.user_id == user_id, Feedback.model_id != None, Feedback.dataset_id != None)
            .all()
        )


feedback = CRUDFeedback(Feedback)
