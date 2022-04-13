from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core import utils
from app.tests.utils.user import create_random_user
from app.core.config import settings
from app.schemas.user import UserCreate
from app.tests.utils.utils import random_email, random_lower_string


def test_get_users_superuser_me(
    client: TestClient, superuser_token_headers: Dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json().get("user")
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["role"]["id"] == 1
    assert current_user["email"] == settings.FIRST_SUPERUSER


def test_get_users_normal_user_me(
    client: TestClient, tester_user_token_headers: Dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=tester_user_token_headers)
    current_user = r.json().get("user")
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["role"]["id"] != 1
    assert current_user["email"] == settings.EMAIL_TESTER_USER


def test_create_user_new_email(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "user_id": username}
    r = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert 200 <= r.status_code < 300
    created_user = r.json()
    user = crud.user.get_by_email(db, email=username)
    assert user
    assert user.email == created_user["email"]


def test_create_user_open_signup(
    client: TestClient, db: Session
) -> None:
    username = random_email()
    password = random_lower_string()
    displayname = random_lower_string()
    token = utils.generate_signup_token(settings.FIRST_SUPERUSER, username)
    data = {"email": username, "password": password, "user_id": username,
            "display_name": displayname, "token": token}
    r = client.post(
        f"{settings.API_V1_STR}/users/open", json=data,
    )
    assert 200 <= r.status_code < 300
    created_user = r.json()
    user = crud.user.get_by_email(db, email=username)
    assert user
    assert user.email == created_user["email"]
    assert user.display_name == created_user["display_name"]
    assert user.user_id == created_user["user_id"]


def test_create_user_open_signup_no_token(
    client: TestClient, memory_db: Session
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "user_id": username}
    r = client.post(f"{settings.API_V1_STR}/users/open", json=data)
    assert r.status_code >= 400
    assert "user_id" not in r.json()


def test_create_user_open_signup_bad_token(
    client: TestClient, memory_db: Session
) -> None:
    username = random_email()
    password = random_lower_string()
    token = utils.generate_signup_token(random_email(), random_email())
    data = {"email": username, "password": password, "user_id": username, "token": token}
    r = client.post(f"{settings.API_V1_STR}/users/open", json=data)
    assert r.status_code >= 400
    assert "user_id" not in r.json()


def test_get_existing_user(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    user = create_random_user(db)
    user_id = user.id
    r = client.get(
        f"{settings.API_V1_STR}/users/{user_id}", headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = crud.user.get_by_email(db, email=user.email)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_create_user_existing_email(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    email = random_email()
    userid = random_lower_string()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, user_id=userid)
    crud.user.create(db, obj_in=user_in)
    data = {"email": email, "password": password, "user_id": random_lower_string()}
    r = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert r.status_code == 400
    created_user = r.json()
    assert "_id" not in created_user


def test_create_user_existing_userid(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    email = random_email()
    userid = random_lower_string()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, user_id=userid)
    crud.user.create(db, obj_in=user_in)
    data = {"email": random_email(), "password": password, "user_id": userid}
    r = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data,
    )
    assert r.status_code == 400
    created_user = r.json()
    assert "_id" not in created_user


def test_create_existing_userid_open_registration(
    client: TestClient, memory_db: Session
) -> None:
    email = random_email()
    userid = random_lower_string()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, user_id=userid)
    crud.user.create(memory_db, obj_in=user_in)
    token = utils.generate_signup_token(settings.FIRST_SUPERUSER, email)
    data = {"email": random_email(), "password": password, "user_id": userid, "token": token}
    r = client.post(
        f"{settings.API_V1_STR}/users/open", json=data,
    )
    assert r.status_code == 400
    assert "user_id" not in r.json()


def test_create_user_by_normal_user(
    client: TestClient, tester_user_token_headers: Dict[str, str]
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "user_id": username}
    r = client.post(
        f"{settings.API_V1_STR}/users/", headers=tester_user_token_headers, json=data,
    )
    assert r.status_code == 403


def test_retrieve_users(
    client: TestClient, superuser_token_headers: dict, memory_db: Session
) -> None:
    create_random_user(memory_db)
    create_random_user(memory_db)

    r = client.get(f"{settings.API_V1_STR}/users/", headers=superuser_token_headers)
    all_users = r.json()

    assert len(all_users) > 1
    for item in all_users:
        assert "email" in item


def test_delete_user_by_superuser(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    id = create_random_user(db).id
    r = client.delete(
        f"{settings.API_V1_STR}/users/{id}", headers=superuser_token_headers
    )
    assert 200 <= r.status_code < 300
    user = crud.user.get(db, id)
    assert not user.is_active


def test_delete_user_by_normal_user(
    client: TestClient, tester_user_token_headers: dict, memory_db: Session
) -> None:
    id = create_random_user(memory_db).id
    r = client.delete(
        f"{settings.API_V1_STR}/users/{id}", headers=tester_user_token_headers
    )
    assert r.status_code == 403
    user = crud.user.get(memory_db, id)
    assert user.is_active


def test_edit_email_new(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    id = create_random_user(db).id
    new_email = random_email()
    r = client.put(
        f"{settings.API_V1_STR}/users/{id}",
        headers=superuser_token_headers,
        json={"email": new_email}
    )
    assert 200 <= r.status_code < 300
    user = crud.user.get(db, id)
    assert user.email == new_email


def test_edit_email_already_existing(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    new_user = create_random_user(db)
    id = new_user.id
    email = new_user.email
    r = client.put(
        f"{settings.API_V1_STR}/users/{id}",
        headers=superuser_token_headers,
        json={"email": settings.FIRST_SUPERUSER}
    )
    assert r.status_code == 400
    user = crud.user.get(db, id)
    assert user.email == email
