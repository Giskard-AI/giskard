import logging
import random
from typing import Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.core.security import verify_password
from app.ee.models.license import LicenseError, ENTERPRISE, BASIC
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.users_service import UsersService
from app.tests.utils.utils import random_email, random_lower_string
import pytest


def _create_user(user_service: UsersService) -> Tuple[User, UserCreate]:
    current_user_count = user_service.db.query(User).count()
    logging.info(f'Number of users before: {current_user_count}')
    email = random_email()
    password = random_lower_string()
    user_id = random_lower_string()
    role_id = random.randint(1, 3)
    user_in = UserCreate(email=email, password=password, role_id=role_id, user_id=user_id)
    user = user_service.create_user(user_in)
    return user, user_in


def test_create_user(user_service: UsersService) -> None:
    user, user_in = _create_user(user_service)
    assert user.email == user_in.email
    assert hasattr(user, "hashed_password")


def test_create_user_basic_plan(user_service: UsersService) -> None:
    settings.ACTIVE_PLAN = BASIC
    for _ in range(BASIC.max_users):
        _create_user(user_service)
    verify_max_seats_exceeded(user_service)


def test_create_user_enterprise_plan(user_service: UsersService) -> None:
    settings.ACTIVE_PLAN = ENTERPRISE
    for _ in range(10):
        _create_user(user_service)


def test_create_user_deactivated_limit(user_service: UsersService) -> None:
    settings.ACTIVE_PLAN = BASIC
    logging.info("TEST test_create_user_deactivated_limit")
    # Creating maximum users allowed by a license
    for _ in range(BASIC.max_users):
        _create_user(user_service)
    db = user_service.db

    # Deactivate one user
    user: User = db.query(User).first()
    user.is_active = False
    crud.user.update(db, db_obj=user, obj_in=UserUpdate(is_active=False))

    # Create yet another user for the deactivated seat
    _create_user(user_service)

    verify_max_seats_exceeded(user_service)


def verify_max_seats_exceeded(user_service):
    with pytest.raises(LicenseError, match='.*Maximum number of users reached for a current license type.*'):
        _create_user(user_service)


def test_authenticate_user(memory_db: Session, user_service: UsersService) -> None:
    user, user_in = _create_user(user_service)
    # authenticate with email
    authenticated_user_1 = crud.user.authenticate(memory_db, username=user_in.email, password=user_in.password)
    assert authenticated_user_1
    assert user.user_id == authenticated_user_1.user_id
    # authenticate with User ID
    authenticated_user_2 = crud.user.authenticate(memory_db, username=user_in.user_id, password=user_in.password)
    assert authenticated_user_2
    assert user.email == authenticated_user_2.email


def test_not_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.user.authenticate(db, username=email, password=password)
    assert user is None


def test_check_if_user_is_active(user_service: UsersService) -> None:
    user, _ = _create_user(user_service)
    is_active = crud.user.is_active(user)
    assert is_active is True


def test_check_if_user_is_active_inactive(user_service: UsersService) -> None:
    user, _ = _create_user(user_service)
    is_active = crud.user.is_active(user)
    assert is_active


def test_check_if_user_is_superuser(db: Session) -> None:
    is_superuser = _create_user_with_role(db, settings.UserRole.ADMIN.value)
    assert is_superuser is True


def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    is_superuser = _create_user_with_role(db, settings.UserRole.AI_TESTER.value)
    assert is_superuser is False


def _create_user_with_role(db, role):
    email = random_email()
    password = random_lower_string()
    user_id = random_lower_string()
    user_in = UserCreate(email=email, password=password, user_id=user_id, role_id=role)
    user = crud.user.create(db, obj_in=user_in)
    is_superuser = crud.user.is_superuser(user)
    return is_superuser


def test_get_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_id = random_lower_string()
    user_in = UserCreate(email=email, password=password, user_id=user_id)
    user = crud.user.create(db, obj_in=user_in)
    user_2 = crud.user.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_get_user_by_email_case_insensitive(db: Session) -> None:
    email_upper = random_email().upper()
    password = random_lower_string()
    user_id = random_lower_string()
    user_in = UserCreate(email=email_upper, password=password, user_id=user_id)
    user = crud.user.create(db, obj_in=user_in)
    user_upper = crud.user.get_by_email(db, email=email_upper)
    user_lower = crud.user.get_by_email(db, email=email_upper.lower())
    assert user_upper
    assert user_lower
    assert user.email == user_lower.email == user_upper.email
    assert jsonable_encoder(user) == jsonable_encoder(user_lower) == jsonable_encoder(user_upper)


def test_update_user_name(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_id = random_lower_string()
    user_in = UserCreate(email=email, password=password, user_id=user_id, role_id=settings.UserRole.ADMIN.value)
    user = crud.user.create(db, obj_in=user_in)
    new_name = random_lower_string()
    user_in_update = UserUpdate(display_name=new_name)
    crud.user.update(db, db_obj=user, obj_in=user_in_update)
    user_2 = crud.user.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert user_2.display_name == new_name


def test_update_user_name_case_insensitive_email(db: Session) -> None:
    email_upper = random_email().upper()
    new_email_upper = random_email().upper()
    password = random_lower_string()
    user_id = random_lower_string()
    user_in = UserCreate(email=email_upper, password=password, user_id=user_id, role_id=settings.UserRole.ADMIN.value)
    user = crud.user.create(db, obj_in=user_in)
    new_name = random_lower_string()
    user_in_update = UserUpdate(display_name=new_name, email=new_email_upper)
    crud.user.update(db, db_obj=user, obj_in=user_in_update)
    user_2 = crud.user.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email == new_email_upper.lower()
    assert user_2.display_name == new_name


def test_update_user_password(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_id = random_lower_string()
    user_in = UserCreate(email=email, password=password, user_id=user_id, role_id=settings.UserRole.ADMIN.value)
    user = crud.user.create(db, obj_in=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password)
    crud.user.update(db, db_obj=user, obj_in=user_in_update)
    user_2 = crud.user.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)
