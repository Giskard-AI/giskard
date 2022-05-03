import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship, declared_attr

from app.db.base_class import Base


class Inspection(Base):
    __tablename__ = "inspection"

    id = Column(Integer, primary_key=True, index=True)
    @declared_attr
    def model_id(cls):
        return Column(Integer, ForeignKey("project_models.id"), nullable=False)
    @declared_attr
    def dataset_id(cls):
        return Column(Integer, ForeignKey("datasets.id"), nullable=False)

    created_on = Column(DateTime(timezone=True), default=datetime.datetime.now)
    location = Column(String, nullable=False)