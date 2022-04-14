from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.feedback_reply import FeedbackReply
from app.schemas.feedback_reply import FeedbackReplyCreateSchema


class CRUDFeedbackReply(CRUDBase[FeedbackReply, FeedbackReplyCreateSchema, FeedbackReplyCreateSchema]):

    def create(
        self, db: Session, obj_in: FeedbackReplyCreateSchema, feedback_id:int, user_id: int
    ) -> FeedbackReply:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, feedback_id=feedback_id, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


feedback_reply = CRUDFeedbackReply(FeedbackReply)
