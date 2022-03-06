from typing import Any, List
import os
import time
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()

logger = logging.getLogger("projects-api")
logger.setLevel(logging.INFO)


@router.get("/", response_model=List[schemas.ProjectSchema])
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve projects that user can access.
    """
    if crud.user.is_superuser(current_user):
        # return all if admin
        projects = crud.project.get_all(db, skip=skip, limit=limit)
    else:
        # return self-owned, and where invited
        projects = crud.project.get_all_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        ) + crud.project.get_all_by_guest(db, current_user.id, skip, limit)
    return projects


@router.post("/", response_model=schemas.ProjectSchema)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new project.
    """
    if current_user.role_id == settings.UserRole.AI_TESTER.value:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")
    project_in.name = project_in.name.strip()
    project_in.description = project_in.description.strip()
    try:
        project = crud.project.create(db, project_in, current_user.id)
        return project
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status.HTTP_400_BAD_REQUEST, type(e).__name__)


@router.put("/{id}", response_model=schemas.ProjectSchema)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    project_in: schemas.ProjectUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an project.
    """
    project = crud.project.get(db=db, id=id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if not crud.user.is_superuser(current_user) and (project.owner_id != current_user.id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")
    project = crud.project.update(db=db, db_obj=project, obj_in=project_in)
    return project


@router.get("/{id}", response_model=schemas.ProjectSchema)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get project by ID.
    """
    project = crud.project.get(db=db, id=id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if (
        not crud.user.is_superuser(current_user)
        and (project.owner_id != current_user.id)
        and current_user.user_id not in [u.user_id for u in project.guest_list]
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")
    return project


@router.delete("/{id}", response_model=schemas.Msg)
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a project.
    """
    project = crud.project.get(db=db, id=id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if not crud.user.is_superuser(current_user) and (project.owner_id != current_user.id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")
    crud.project.remove(db=db, id=id)
    return {"msg": "Deleted"}


@router.put("/{id}/invite", response_model=schemas.ProjectSchema)
def invite_user_to_project(
    db: Session = Depends(deps.get_db),
    *,
    id: int,
    user_id: str = Body(..., embed=True),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a project by inviting a user as guest.
    """
    project = crud.project.get(db, id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions to invite user")

    user = crud.user.get_by_userid(db, userid=user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    elif user.id == project.owner_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot invite self")
    elif user_id in [u.user_id for u in project.guest_list]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User already invited to project")

    project = crud.project.add_guest_to_project(db, project, user)
    return project

@router.put("/{id}/uninvite", response_model=schemas.ProjectSchema)
def uninvite_user_from_project(
    db: Session = Depends(deps.get_db),
    *,
    id: int,
    user_id: str = Body(..., embed=True),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a project by uninviting a user as guest.
    """
    project = crud.project.get(db, id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if project.owner_id != current_user.id and not crud.user.is_superuser(current_user):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions to uninvite user")

    user = crud.user.get_by_userid(db, userid=user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    elif user_id not in [u.user_id for u in project.guest_list]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User not in project")

    project = crud.project.remove_guest_from_project(db, project, user)
    return project


@router.get("/{id}/models", response_model=List[schemas.ProjectModelFileSchema])
def read_project_models(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    project = crud.project.get(db, id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    elif (
        not crud.user.is_superuser(current_user)
        and (project.owner_id != current_user.id)
        and current_user.user_id not in [u.user_id for u in project.guest_list]
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")

    models = crud.project_model.get_all_by_project(db, project_id=id)
    model_files_for_gui = [
        schemas.ProjectModelFileSchema(
            id=m.id,
            name=m.file_name.replace(".pkl.zst", ""),
            python_version=m.python_version,
            size=os.path.getsize(m.location),
            creation_date=m.created_on,
            project_id=m.project_id)
        for m in models]
    return model_files_for_gui


@router.get("/{id}/datasets", response_model=List[schemas.ProjectFileSchema])
def read_project_datasets(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get datasets files in a project
    """
    project = crud.project.get(db, id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    elif (
        not crud.user.is_superuser(current_user)
        and (project.owner_id != current_user.id)
        and current_user.user_id not in [u.user_id for u in project.guest_list]
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")

    files = crud.dataset.get_all_by_project(db, project_id=id)
    files_for_gui = [
        schemas.ProjectFileSchema(
            id=f.id,
            name=f.file_name.replace(".zst", ""),
            size=os.path.getsize(f.location),
            creation_date=f.created_on,
            project_id=f.project_id)
        for f in files]
    return files_for_gui
