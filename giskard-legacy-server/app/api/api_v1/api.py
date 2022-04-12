from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    files,
    prediction_models,
    projects,
    login,
    users,
    utils,
    roles,
    third_party,
    feedbacks
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(prediction_models.router, prefix="/models", tags=["models"])
api_router.include_router(third_party.router, prefix="/third-party", tags=["external library"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(feedbacks.router, prefix="/feedbacks", tags=["models", "feedbacks"])
