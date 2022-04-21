from app.core.config import settings
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from app.db.base_class import Base

if TYPE_CHECKING:
    from .role import Role  # noqa: F401


class User(Base):
    __tablename__ = "giskard_users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    role_id = Column(Integer, ForeignKey("role.id"), default=settings.UserRole.AI_TESTER.value)
    role = relationship("Role")
