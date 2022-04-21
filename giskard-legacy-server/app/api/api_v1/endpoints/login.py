from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.utils import (
    send_reset_password_email,
    verify_password_reset_token,
)

router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect credentials")
    elif not crud.user.is_active(user):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "User has been disabled. Please contact system administrator.")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.user_id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=schemas.UserSchema)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{userId}", response_model=schemas.Msg)
def recover_password(userId: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Password Recovery
    """
    user = crud.user.get_by_userid(db, userid=userId)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sorry, this user ID does not exist")

    send_reset_password_email(user.email)
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password/", response_model=schemas.Msg)
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")

    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            "Token matches no existing user")
    elif not crud.user.is_active(user):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User is disabled")

    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}


@router.get("/security/api-access-token", response_model=schemas.Token, status_code=201)
def get_api_access_token(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate a token for third party software access
    """
    token = security.create_api_access_token(current_user.user_id)
    return {
        "access_token": token,
        "token_type": "api_key"
    }
