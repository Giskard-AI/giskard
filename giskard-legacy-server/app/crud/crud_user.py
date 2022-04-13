from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower()).first()

    def get_by_userid(self, db: Session, *, userid: str) -> Optional[User]:
        return db.query(User).filter(User.user_id == userid).first()

    def get_active_user_count(self, db: Session):
        return db.query(User).filter(User.is_active == True).count()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            user_id=obj_in.user_id,
            role_id=obj_in.role_id,
            display_name=obj_in.display_name
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    # Username can be either User ID or Email
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=username) or self.get_by_userid(db, userid=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.role_id == settings.UserRole.ADMIN.value


user = CRUDUser(User)
