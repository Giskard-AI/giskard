from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.tests.utils.utils import random_email, random_lower_string


def get_first_admin_user(db: Session):
    return crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)


def get_ai_creator_user(db: Session):
    creator = crud.user.get_by_email(db, email=settings.EMAIL_CREATOR_USER)
    # create if not present
    if not creator:
        user_in_create = UserCreate(
            user_id="ai_creator",
            email=settings.EMAIL_CREATOR_USER,
            password=random_lower_string(),
            role_id=settings.UserRole.AI_CREATOR.value
        )
        creator = crud.user.create(db, obj_in=user_in_create)
    return creator


def get_ai_tester_user(db: Session):
    tester = crud.user.get_by_email(db, email=settings.EMAIL_TESTER_USER)
    # create if not present
    if not tester:
        user_in_create = UserCreate(
            user_id="ai_tester",
            email=settings.EMAIL_TESTER_USER,
            password=random_lower_string(),
            role_id=settings.UserRole.AI_TESTER.value
        )
        tester = crud.user.create(db, obj_in=user_in_create)
    return tester


def get_superuser_token_headers(client: TestClient) -> Dict[str, str]:
    return user_authentication_headers(
        client=client,
        email=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD
    )


def get_token_headers_for_user(
    client: TestClient, db: Session, user: User,
) -> Dict[str, str]:
    """
    Caution: resets user password at every run because it is needed for the authentication request
    """
    password = random_lower_string()
    user_in_update = UserUpdate(password=password)
    user = crud.user.update(db, db_obj=user, obj_in=user_in_update)
    return user_authentication_headers(client=client, email=user.email, password=password)


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> Dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(db: Session) -> User:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(user_id=username, email=username, password=password)
    user = crud.user.create(db=db, obj_in=user_in)
    return user
