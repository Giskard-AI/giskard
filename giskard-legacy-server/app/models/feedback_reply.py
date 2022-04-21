import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class FeedbackReply(Base):
    __tablename__ = "feedback_replies"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey("feedbacks.id", ondelete="CASCADE"), nullable=False, index=True)
    reply_to_reply = Column(Integer, ForeignKey("feedback_replies.id", ondelete="CASCADE"), default=None, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("giskard_users.id"), nullable=False)
    user = relationship('User')
    content = Column(String)
    created_on = Column(DateTime(timezone=True), default=datetime.datetime.now)
