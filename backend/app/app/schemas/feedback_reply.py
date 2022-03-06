from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.user import UserMinimalSchema


class FeedbackReplySchema(BaseModel):
    id: int
    reply_to_reply: Optional[int]
    content: str
    user: UserMinimalSchema
    created_on: datetime

    class Config:
	    orm_mode=True


class FeedbackReplyCreateSchema(BaseModel):
    content: str
    reply_to_reply: Optional[int]
