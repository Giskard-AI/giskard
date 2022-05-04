from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import utils
from app.core.base_model import CaseInsensitiveEmailStr
from app.core.config import settings
from app.models.config import AppUserConfig, AppConfig
from app.schemas import UserSchema
from app.services.users_service import UsersService

router = APIRouter()


# @router.get("/", response_model=List[schemas.UserSchema])
# def read_users(
#     db: Session = Depends(deps.get_db),
#     skip: int = 0,
#     limit: int = 100,
#     current_user: models.User = Depends(deps.get_current_active_superuser),
# ) -> Any:
#     """
#     Retrieve users.
#     """
#     users = crud.user.get_all(db, skip=skip, limit=limit)
#     return users


# @router.post("/", response_model=schemas.UserSchema)
# def create_user(
#     *,
#     user_service: UsersService = Depends(),
#     user_in: schemas.UserCreate,
#     current_user: models.User = Depends(deps.get_current_active_superuser),
# ) -> Any:
#     """
#     Create new user (from admin side)
#     """
#     user = user_service.create_user(user_in)
#
#     if settings.EMAILS_ENABLED and user_in.email:
#         utils.send_new_account_email(email_to=user_in.email, new_user_id=user_in.user_id)
#     return user


@router.put("/me", response_model=schemas.UserSchema)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    password: str = Body(None),
    display_name: str = Body(None),
    email: CaseInsensitiveEmailStr = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    if email is not None and crud.user.get_by_email(db, email=email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "A user with this email already exists in the system")

    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if display_name is not None:
        user_in.display_name = display_name
    if email is not None:
        user_in.email = email
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/me", response_model=AppUserConfig)
def read_user_me(
        current_user: models.User = Depends(deps.get_current_active_user),
        user_service: UsersService = Depends()
) -> Any:
    """
    Get current user.
    """
    app_config = AppConfig(plan_code=settings.ACTIVE_PLAN.code,
                           plan_name=settings.ACTIVE_PLAN.display_name,
                           seats_available=user_service.get_available_seats())
    return AppUserConfig(app=app_config, user=UserSchema.from_orm(current_user))


@router.get("/me/coworkers", response_model=List[schemas.UserMinimalSchema])
def read_other_users_minimal_info(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve list of other users minimal info like id and display name
    """
    users = crud.user.get_all(db, skip=skip, limit=limit)
    users.remove(current_user)
    active_users = [u for u in users if u.is_active]
    return active_users


@router.post("/invite", response_model=schemas.Msg, status_code=201)
def invite_user_to_signup(
    email: CaseInsensitiveEmailStr = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Send email and signup link with token, for external users to signup
    """
    if email == current_user.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot invite self")

    if crud.user.get_by_email(db, email=email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This email is already registered")

    utils.send_invite_email(email, current_user.email, current_user.user_id)
    return {"msg": "Email invite successfully sent"}


@router.get("/signuplink", response_model=schemas.Msg, status_code=201)
def get_signup_link(
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Generate a signup link with token, for external users to signup
    """
    token = utils.generate_signup_token(current_user.email)
    link = f"{settings.SERVER_HOST}/auth/signup?token={token}"
    return {"msg": link}


@router.post("/open", response_model=schemas.UserSchema)
def create_user_open(
        *,
        db: Session = Depends(deps.get_db),
        token: str = Body(...),
        password: str = Body(...),
        email: CaseInsensitiveEmailStr = Body(...),
        user_id: str = Body(...),
        display_name: str = Body(None),
        user_service: UsersService = Depends()
) -> Any:
    """
    Create new user, for self registration
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Open user registration is forbidden on this server")

    # checking token integrity
    if not utils.decode_signup_token(token):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")

    # check issuer email in token (should always be present, and should be an admin)
    issuer_email = utils.decode_signup_token(token)[0]
    if not issuer_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token, no issuer")
    issuer = crud.user.get_by_email(db, email=issuer_email)
    if not issuer or not crud.user.is_active(issuer) or not crud.user.is_superuser(issuer):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Invalid token issuer")

    # check recipient email in token. Should only be present in case of email invite
    recipient_email = utils.decode_signup_token(token)[1]
    if recipient_email and not recipient_email == email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token recipient")

    user_in = schemas.UserCreate(
        password=password, email=email, user_id=user_id, display_name=display_name
    )
    user = user_service.create_user(user_in)
    return user


@router.get("/{id}", response_model=schemas.UserSchema)
def read_user_by_id(
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "User doesn't have enough privileges")
    return user


@router.put("/{id}", response_model=schemas.UserSchema)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    if user_in.email is not None and crud.user.get_by_email(db, email=user_in.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "A user with this email already exists in the system")
    user_to_update = crud.user.get(db, id=id)
    if not user_to_update:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "No user with this ID in the system")

    user = crud.user.update(db, db_obj=user_to_update, obj_in=user_in)
    return user


@router.delete("/{id}", response_model=schemas.UserSchema)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a user => atually flagging it as not active
    """
    user_to_update = crud.user.get(db, id=id)
    if not user_to_update:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "No user with this ID in the system")

    user = crud.user.update(db, db_obj=user_to_update, obj_in={"is_active": False})
    return user
