from sqlalchemy.orm import Session

from app import crud
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.tests.utils.utils import random_lower_string
from app.tests.utils.user import get_ai_tester_user


def test_create_project(db: Session) -> None:
    name = random_lower_string()
    description = random_lower_string()
    project_in = ProjectCreate(name=name, description=description)
    project = crud.project.create(db, project_in, 1)
    assert project.name == name
    assert project.description == description
    assert project.owner_id == 1


def test_get_project(db: Session) -> None:
    name = random_lower_string()
    description = random_lower_string()
    project_in = ProjectCreate(name=name, description=description)
    project = crud.project.create(db, project_in, 1)
    stored_project = crud.project.get(db=db, id=project.id)
    assert stored_project
    assert project.id == stored_project.id
    assert project.name == stored_project.name
    assert project.description == stored_project.description
    assert project.owner_id == 1


def test_update_project(db: Session) -> None:
    name = random_lower_string()
    description = random_lower_string()
    project_in = ProjectCreate(name=name, description=description)
    project = crud.project.create(db, project_in, 1)
    name2 = random_lower_string()
    description2 = random_lower_string()
    project_update = ProjectUpdate(name=name2, description=description2)
    project2 = crud.project.update(db=db, db_obj=project, obj_in=project_update)
    assert project.id == project2.id
    assert project2.name == name2
    assert project2.description == description2
    assert project.owner_id == 1


def test_delete_project(db: Session) -> None:
    name = random_lower_string()
    description = random_lower_string()
    project_in = ProjectCreate(name=name, description=description)
    project = crud.project.create(db, project_in, 1)
    project2 = crud.project.remove(db=db, id=project.id)
    assert project2.id == project.id
    assert project2.name == name
    assert project2.description == description
    assert project2.owner_id == 1
    project3 = crud.project.get(db=db, id=project.id)
    assert project3 is None


def test_invite_guest_to_project(db: Session) -> None:
    project_in = ProjectCreate(name=random_lower_string(), description=random_lower_string())
    project = crud.project.create(db, project_in, 1)
    test_user = get_ai_tester_user(db)
    project_out = crud.project.add_guest_to_project(db, project, test_user)
    assert len(project_out.guest_list) > 0
    assert project_out.guest_list[0].user_id == test_user.user_id
    assert len(crud.project.get_all_by_guest(db, test_user.id)) > 0
