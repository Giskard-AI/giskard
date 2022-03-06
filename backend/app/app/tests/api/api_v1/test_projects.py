from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.tests.utils.project import create_random_project
from app.tests.utils.user import (create_random_user, get_first_admin_user, get_ai_creator_user, 
                                  get_ai_tester_user)


def test_create_project_as_superuser(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    data = {"name": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/projects/", headers=superuser_token_headers, json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content
    assert "owner_details" in content


def test_create_project_as_creator(
    client: TestClient, creator_user_token_headers: dict, db: Session
) -> None:
    data = {"name": "Foo", "description": "Fighters by AICreator"}
    response = client.post(
        f"{settings.API_V1_STR}/projects/", headers=creator_user_token_headers, json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert "owner_id" in content and content["owner_id"] == get_ai_creator_user(db).id
    assert "id" in content


def test_create_project_as_tester(
    client: TestClient, tester_user_token_headers: dict, db: Session
) -> None:
    data = {"name": "FooBar", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/projects/", headers=tester_user_token_headers, json=data,
    )
    assert response.status_code == 401
    assert "created_on" not in response.json()


def test_read_own_project_as_creator(
    client: TestClient, creator_user_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}", headers=creator_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == project.name
    assert content["description"] == project.description
    assert content["id"] == project.id
    assert content["owner_id"] == project.owner_id


def test_read_project_as_admin(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == project.name
    assert content["description"] == project.description
    assert content["id"] == project.id
    assert content["owner_id"] == project.owner_id


def test_read_all_projects_as_admin(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    create_random_project(db, owner_id=get_ai_creator_user(db).id)
    create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/", headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_read_someone_else_projects_as_tester_not_invited(
    client: TestClient, tester_user_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}", headers=tester_user_token_headers,
    )
    assert response.status_code == 401


def test_update_project_as_creator(
    client: TestClient, creator_user_token_headers: dict, db: Session
) -> None:
    project_id = create_random_project(db, owner_id=get_ai_creator_user(db).id).id
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project_id}", headers=creator_user_token_headers,
        json={"name": "Bla", "description": "Blablabla"},
    )
    assert response.status_code == 200
    project = crud.project.get(db, project_id)
    assert project.name == "Bla"
    assert project.description == "Blablabla"


def test_update_project_as_admin(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    project_id = create_random_project(db, owner_id=get_ai_creator_user(db).id).id
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project_id}", headers=superuser_token_headers,
        json={"description": "Blablabla"},
    )
    assert response.status_code == 200
    project = crud.project.get(db, project_id)
    assert project.description == "Blablabla"


def test_update_project_as_tester(
    client: TestClient, tester_user_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}", headers=tester_user_token_headers,
        json={"description": "Blablabla"},
    )
    assert response.status_code == 401
    project = crud.project.get(db, project.id)
    assert project.description != "Blablabla"


def test_delete_project_as_creator(
    client: TestClient, creator_user_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}", headers=creator_user_token_headers
    )
    assert response.status_code == 200
    project_db = crud.project.get(db, project.id)
    assert project_db is None


def test_delete_project_as_admin(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Deleted"
    project_db = crud.project.get(db, project.id)
    assert project_db is None


def test_delete_project_as_tester(
    client: TestClient, tester_user_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project.id}", headers=tester_user_token_headers
    )
    assert response.status_code == 401
    project_db = crud.project.get(db, project.id)
    assert project_db is not None


def test_invite_someone_to_own_project(
    client: TestClient, creator_user_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/invite", headers=creator_user_token_headers,
        json={"user_id": get_ai_creator_user(db).user_id}
    )
    assert response.status_code == 400  # cannot invite self

    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/invite", headers=creator_user_token_headers,
        json={"user_id": get_ai_tester_user(db).user_id}
    )
    assert response.status_code == 200
    project = crud.project.get(db, project.id)
    assert len(project.guest_list) > 0
    assert project.guest_list[0].user_id == get_ai_tester_user(db).user_id


def test_invite_someone_to_project_as_non_owner(  # in this case, as admin
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/invite", headers=superuser_token_headers,
        json={"user_id": get_ai_tester_user(db).user_id}
    )
    assert response.status_code == 401  # unauthorized because not enough permissions
    project = crud.project.get(db, project.id)
    assert len(project.guest_list) == 0


def test_invite_someone_to_project_as_test_user(
    client: TestClient, tester_user_token_headers: dict, db: Session
) -> None:
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    user3 = create_random_user(db)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/invite", headers=tester_user_token_headers,
        json={"user_id": user3.user_id}
    )
    assert response.status_code == 401  # unauthorized because not enough permissions
    project = crud.project.get(db, project.id)
    assert len(project.guest_list) == 0


def test_read_projects_invited_to_as_test_user(
    client: TestClient, creator_user_token_headers: dict, tester_user_token_headers: dict, 
    db: Session
) -> None:
    # create and invite
    project = create_random_project(db, owner_id=get_ai_creator_user(db).id)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/invite", headers=creator_user_token_headers,
        json={"user_id": get_ai_tester_user(db).user_id}
    )
    assert response.status_code == 200

    # get all projects as tester, should be more than 0
    response_read_all = client.get(
        f"{settings.API_V1_STR}/projects", headers=tester_user_token_headers
    )
    assert response_read_all.status_code == 200
    assert len(response_read_all.json()) > 0

    # get specific project invited to
    response_read = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}", headers=tester_user_token_headers
    )
    assert response_read.status_code == 200
    response_read_content = response_read.json()
    assert response_read_content["name"] == project.name
    assert response_read_content["owner_id"] == project.owner_id


def test_read_all_projects_invited_to_as_creator(
    client: TestClient, superuser_token_headers: dict, creator_user_token_headers: dict, db: Session
) -> None:
    # create and invite
    project = create_random_project(db, get_first_admin_user(db).id)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.id}/invite", headers=superuser_token_headers,
        json={"user_id": get_ai_creator_user(db).user_id}
    )
    assert response.status_code == 200

    # create another project as self
    create_random_project(db, get_ai_creator_user(db).id)
    # get all projects as creator, should be more than 1
    response_read_all = client.get(
        f"{settings.API_V1_STR}/projects", headers=creator_user_token_headers
    )
    assert response_read_all.status_code == 200
    assert len(response_read_all.json()) > 1
