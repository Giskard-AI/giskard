from typing import List, Optional
from pathlib import Path
import shutil

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.crud.base import CRUDBase
from app.models.project import Project, association_table
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.core import utils, config


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create(
        self, db: Session, obj_in: ProjectCreate, owner_id: int
    ) -> Project:
        obj_in_data = jsonable_encoder(obj_in)
        generated_key = utils.transmogrify(obj_in.name)
        if generated_key:
            # if key already exist, increment
            nb_similar_keys = len(self.get_similar_keys(db, generated_key))
            if nb_similar_keys > 0:
                generated_key += "-" + str(nb_similar_keys)
            db_obj = self.model(**obj_in_data, owner_id=owner_id, key=generated_key)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        else:
            raise ValueError("Empty project key")

    def get_by_key(
        self, db: Session, query_key: str
    ) -> Optional[Project]:
        return db.query(self.model).filter(self.model.key == query_key).first()

    def get_similar_keys(
        self, db: Session, query_key: str
    ) -> List[Project]:
        """Applies a regular expression for project keys starting with the query and ending with "-{number}".

        Also counts if there is an exact match between the query and an existing project key.
        The ~ op is the regular expression operator, which is *only valid for PostgreSQL*.
        """
        return (
            db.query(self.model)
            .filter(or_(Project.key.op("~")(f"^{query_key}-\\d+$"), Project.key == query_key))
            .all()
        )

    def get_all_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        return (
            db.query(self.model)
            .filter(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_by_guest(
        self, db: Session, id: int, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        return (
            db.query(self.model)
            .join(association_table, User)
            .filter(User.id == id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def add_guest_to_project(
        self, db: Session, project_obj: Project, user_obj: User
    ) -> Project:
        project_obj.guest_list.append(user_obj)
        db.add(project_obj)
        db.commit()
        db.refresh(project_obj)
        return project_obj

    def remove_guest_from_project(
        self, db: Session, project_obj: Project, user_obj: User
    ) -> Project:
        project_obj.guest_list.remove(user_obj)
        db.add(project_obj)
        db.commit()
        db.refresh(project_obj)
        return project_obj

    def remove(self, db: Session, *, id: int) -> Project:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        # delete project directory and all files
        project_file_path = Path(config.settings.BUCKET_PATH / obj.key)
        if project_file_path.exists():
            shutil.rmtree(project_file_path)
        return obj


project = CRUDProject(Project)
