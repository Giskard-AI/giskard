import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship

from app.db.base_class import Base

association_table = Table(
    "projects_guests",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("user_id", Integer, ForeignKey("giskard_users.id")),
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, index=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    created_on = Column(DateTime(timezone=True), default=datetime.datetime.now)
    owner_id = Column(Integer, ForeignKey("giskard_users.id"), nullable=False)
    owner_details = relationship("User")
    guest_list = relationship("User", secondary=association_table)
    model_files = relationship("ProjectModel", cascade="all, delete")
    data_files = relationship("Dataset", cascade="all, delete")
