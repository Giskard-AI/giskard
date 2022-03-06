from typing import Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base_class import Base
from app.db.session import SessionLocal
from app.ee.models.license import ENTERPRISE
from app.main import app
from app.services.users_service import UsersService
from app.tests.utils import user


@pytest.fixture(scope="function")
def memory_db() -> Generator:
    engine = create_engine('sqlite://', echo=True)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    Base.metadata.create_all(bind=engine)
    yield session


@pytest.fixture(scope="session")
def db() -> Generator:
    yield SessionLocal()


@pytest.fixture(scope="module")
def client() -> Generator:
    settings.ACTIVE_PLAN = ENTERPRISE
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    return user.get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def creator_user_token_headers(client: TestClient, db: Session) -> Dict[str, str]:
    creator_user = user.get_ai_creator_user(db)
    return user.get_token_headers_for_user(client, db, creator_user)


@pytest.fixture(scope="module")
def tester_user_token_headers(client: TestClient, db: Session) -> Dict[str, str]:
    tester_user = user.get_ai_tester_user(db)
    return user.get_token_headers_for_user(client, db, tester_user)


@pytest.fixture(scope="function")
def user_service(memory_db: Session) -> Generator:
    yield UsersService(memory_db)
