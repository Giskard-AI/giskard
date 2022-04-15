import os
import secrets
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, HttpUrl, PostgresDsn, validator

from app.core.base_model import CaseInsensitiveEmailStr
from app.ee.models.license import Plan, BASIC, PLANS_BY_CODE


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str
    SENTRY_DSN: Optional[HttpUrl] = None

    @validator("SENTRY_DSN", pre=True)
    def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
        if len(v) == 0:
            return None
        return v

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    WELCOME_FROM_EMAIL: Optional[CaseInsensitiveEmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    NOTIFICATION_FROM_EMAIL: Optional[CaseInsensitiveEmailStr] = None

    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if not v:
            return values["PROJECT_NAME"]
        return v

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "email-templates/build"
    EMAILS_ENABLED: bool = False

    @validator("EMAILS_ENABLED", pre=True)
    def get_emails_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:
        return bool(
            values.get("SMTP_HOST")
            and values.get("SMTP_PORT")
            and values.get("WELCOME_FROM_EMAIL")
        )

    EMAIL_TESTER_USER: CaseInsensitiveEmailStr = "aitester@giskard.ai"
    EMAIL_CREATOR_USER: CaseInsensitiveEmailStr = "aicreator@giskard.ai"
    FIRST_SUPERUSER: CaseInsensitiveEmailStr
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool = True

    EMAIL_SIGNUP_TOKEN_EXPIRE_HOURS: int = 72

    class UserRole(Enum):
        ADMIN = 1
        AI_CREATOR = 2
        AI_TESTER = 3

    BUCKET_PATH = Path("files-bucket")

    ACTIVE_PLAN: Plan = BASIC

    @validator("ACTIVE_PLAN", pre=True)
    def active_plan_initializer(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        return PLANS_BY_CODE.get(os.environ.get('GISKARD_PLAN')) or BASIC

    class Config:
        case_sensitive = True

    DEMO_PROJECT_DIR = Path("demo_project")



settings = Settings()
