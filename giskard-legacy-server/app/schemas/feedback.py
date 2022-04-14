from typing import Optional, Dict, Any, List
from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserMinimalSchema
from app.schemas.project_file import ProjectFileMinimalSchema
from app.schemas.feedback_reply import FeedbackReplySchema


class FeedbackBaseSchema(BaseModel):
    feedback_type: str
    feature_name: Optional[str]
    feature_value: Optional[Any]
    feedback_choice: Optional[str]
    feedback_message: Optional[str]


class FeedbackCreateSchema(FeedbackBaseSchema):
    project_id: int
    model_id: int
    dataset_id: int
    target_feature: Optional[str]
    user_data: Dict[str, Any]
    original_data: Dict[str, Any]


class FeedbackSchemaForList(FeedbackBaseSchema):
    id: int
    user_id: str
    model_name: str
    dataset_name: str
    created_on: datetime


class FeedbackSchemaSingle(FeedbackBaseSchema):
    id: int
    user: UserMinimalSchema
    created_on: datetime
    target_feature: Optional[str]
    model: ProjectFileMinimalSchema
    dataset: ProjectFileMinimalSchema
    user_data: Dict[str, Any]
    original_data: Dict[str, Any]
    replies: List[FeedbackReplySchema]
    
    class Config:
	    orm_mode=True