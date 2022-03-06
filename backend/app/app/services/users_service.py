import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.config import settings
from app.ee.models.license import LicenseError
from app.models import User


class UsersService:
    db: Session

    def __init__(self, db: Session = Depends(deps.get_db)) -> None:
        self.db = db

    # todo: combine 2 db calls into 1, replace HTTPException with a lower level exception that doesn't specify http code
    def create_user(self, user_in: schemas.UserCreate) -> User:
        if settings.ACTIVE_PLAN.is_user_number_beyond_limit(crud.user.get_active_user_count(self.db) + 1):
            msg = 'Maximum number of users reached for a current license type'
            logging.warning(msg)
            raise LicenseError(msg)
        user = crud.user.get_by_userid(self.db, userid=user_in.user_id)
        if user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "This user ID is already taken")

        user = crud.user.get_by_email(self.db, email=user_in.email)
        if user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "A user with this email already exists in the system")

        user = crud.user.create(self.db, obj_in=user_in)

        return user

    def get_available_seats(self):
        if settings.ACTIVE_PLAN.max_users is None:
            return None
        return settings.ACTIVE_PLAN.max_users - crud.user.get_active_user_count(self.db)
