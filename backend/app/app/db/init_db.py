import logging
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.api_v1.endpoints.third_party import save_model_file, save_requirements_file
from app.core import files
from app.core.config import settings
from app.db import base  # noqa: F401

# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
from app.schemas import ProjectModelCreateSchema, ProjectFileCreateSchema


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    user = create_superuser(db)

    create_demo_project(db, user)


def create_superuser(db):
    user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
    if not user:
        user_in = schemas.UserCreate(
            email=settings.FIRST_SUPERUSER,
            user_id=settings.FIRST_SUPERUSER.split('@')[0],
            password=settings.FIRST_SUPERUSER_PASSWORD,
            role_id=settings.UserRole.ADMIN.value,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841
    return user


def create_demo_project(db, user):
    logging.info("Creating demo project")
    demo_project = crud.project.get_by_key(db, query_key='giskard-demo-project')
    if demo_project:
        logging.info("Demo project already exists, skipping")
    else:
        project = crud.project.create(
            db,
            schemas.ProjectCreate(
                name="Giskard demo project",
                description="Try working with binary classification model and a credit scoring dataset"),
            user.id
        )
        logging.info(f"Created demo project {project.key}")

        with open(demo_file_path("demo-model.pkl.zst"), "rb") as model_file:
            model_path, storage_dir = save_model_file(model_file, "Demo model", project.key)
        logging.info(f"Created demo model file: {model_path}")

        with open(demo_file_path("demo-model-requirements.txt"), "rb") as model_req_file:
            requirements_path = save_requirements_file("Demo model", model_req_file, storage_dir)
            logging.info(f"Created demo requirement file: {requirements_path}")

            model = crud.project_model.create(
                db,
                ProjectModelCreateSchema(file_name="demo-model.pkl.zst",
                                         location=str(model_path),
                                         python_version="3.7.12",
                                         requirements_file_location=str(requirements_path)),
                project_id=project.id, owner_id=user.id)
            logging.info(f"Created demo model entity {project.key}->{model.id}")

        with open(demo_file_path("demo-dataset.csv.zst"), "rb") as ds_file:
            ds = files.save_dataset_file(db, UploadFile("demo-dataset.csv.zst", BytesIO(ds_file.read())), project,
                                         user.id)
        logging.info(f"Created demo dataset {project.key}->{ds.id} ({ds.location})")
        logging.info(f"Created demo dataset entity {project.key}->{ds.id}")


def demo_file_path(fname):
    return Path(settings.DEMO_PROJECT_DIR) / fname
