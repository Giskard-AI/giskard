import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.sql.sqltypes import JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    model_id = Column(Integer, ForeignKey("project_models.id", ondelete="SET NULL"), index=True)
    model = relationship('ProjectModel')
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), index=True)
    dataset = relationship('Dataset')
    target_feature = Column(String)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship('User')
    created_on = Column(DateTime(timezone=True), default=datetime.datetime.now)
    feedback_type = Column(String, nullable=False, index=True)
    feature_name = Column(String)
    feature_value = Column(String)
    feedback_choice = Column(String)
    feedback_message = Column(String)
    user_data = Column(JSON, nullable=False)
    original_data = Column(JSON, nullable=False)
    replies = relationship('FeedbackReply')
