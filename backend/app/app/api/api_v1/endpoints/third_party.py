import shutil
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Security, File, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core import utils, files
from app.core.config import settings

router = APIRouter()

logger = logging.getLogger("third-party-api")
logger.setLevel(logging.INFO)


@router.post("/models/upload")
def upload_model(
    project_key: str,
    model_name: str,
    python_version: str,
    model: UploadFile = File(...),
    requirements: UploadFile = File(...),
    header: HTTPAuthorizationCredentials = Security(HTTPBearer()),
    db: Session = Depends(deps.get_db),
) -> schemas.ProjectModelFileSchema:
    user_id = utils.verify_api_access_token(header.credentials)
    if not user_id:
        logger.error("Invalid token")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")
    issuer = crud.user.get_by_userid(db, userid=user_id)
    if not issuer or not crud.user.is_active(issuer):
        logger.error("Invalid token issuer")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token issuer")
    if issuer.role_id == settings.UserRole.AI_TESTER.value:
        logger.error("Not enough permissions")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")

    try:  # TODO: define better later what to do with the files
        # if project does not exist (key check), create it
        project = crud.project.get_by_key(db, project_key)
        if not project:
            project = crud.project.create(db, schemas.ProjectCreate(name=project_key), issuer.id)
            project_key = project.key
        elif project.owner_id != issuer.id and issuer.role_id != settings.UserRole.ADMIN.value:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "No permission to upload on this project"
            )

        storageDir = settings.BUCKET_PATH / project_key
        storageDir.mkdir(parents=True, exist_ok=True)

        model_file_name = f"{model_name}.pkl.zst"
        model_path = storageDir / model_file_name
        model_path = files.make_unique_path(model_path, num_file_extensions=2)
        with open(model_path, "wb") as buffer:
            shutil.copyfileobj(model.file, buffer)

        requirements_path = storageDir / f"{model_name}-requirements.txt"
        requirements_path = files.make_unique_path(requirements_path, num_file_extensions=1)
        with open(requirements_path, "wb") as buffer:
            shutil.copyfileobj(requirements.file, buffer)
        # store info in DB
        project_in = schemas.ProjectModelCreateSchema(
            file_name=model_path.stem,
            location=str(model_path),
            python_version=python_version,
            requirements_file_location=str(requirements_path),
        )
        model_out = crud.project_model.create(db, project_in, project.id, issuer.id)
        return model_out

    except Exception as e:
        logger.error(f"Could not upload model to server: {e}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Could not upload model to server. Reason: [{type(e).__name__}] {e}",
        )


@router.post("/data/upload")
def upload_data(
    project_key: str,
    dataset_name: str,
    data_file: UploadFile = File(...),
    header: HTTPAuthorizationCredentials = Security(HTTPBearer()),
    db: Session = Depends(deps.get_db),
) -> schemas.ProjectFileSchema:
    user_id = utils.verify_api_access_token(header.credentials)
    if not user_id:
        logger.error("Invalid token")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")
    issuer = crud.user.get_by_userid(db, userid=user_id)
    if not issuer or not crud.user.is_active(issuer):
        logger.error("Invalid token issuer")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token issuer")

    try:
        project = crud.project.get_by_key(db, project_key)
        if not project:
            project = crud.project.create(db, schemas.ProjectCreate(name=project_key), issuer.id)
            project_key = project.key
        elif project.owner_id != issuer.id and issuer.role_id != settings.UserRole.ADMIN.value:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "No permission to upload on this project"
            )

        data_file.filename = dataset_name
        dataset_out = files.save_dataset_file(db, data_file, project, issuer.id)
        return dataset_out

    except Exception as e:
        logger.error(f"Could not upload data to server: {e}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Could not upload data to server. Reason: [{type(e).__name__}] {e}",
        )
