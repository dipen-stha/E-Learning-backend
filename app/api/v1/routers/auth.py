from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlmodel import Session

from app.api.v1.schemas.auth import Token, TokenRefreshData
from app.api.v1.schemas.users import UserFetchSchema
from app.db.crud.users import get_user_by_id, update_user_login
from app.db.models.users import User
from app.db.session.session import get_db
from app.services.auth.core import (
    authenticate_user,
    create_access_token,
    create_tokens,
    get_current_user,
)


auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login/", response_model=Token)
def login(
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user, _ = authenticate_user(data.username, data.password, db)
        if not user:
            raise HTTPException(
                status_code=401, detail="Incorrect username or password"
            )
        access_token, refresh_token = create_tokens(
            data={"sub": user.username, "scopes": data.scopes},
        )
        _ = update_user_login(user, db)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.post("/admin/login/", response_model=Token)
def admin_login(
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user, _ = authenticate_user(data.username, data.password, db)
        if not user:
            raise HTTPException(
                status_code=401, detail="Incorrect username or password"
            )
        if not user.is_admin and not user.is_superuser:
            raise HTTPException(
                status_code=403, detail="User is not authorized to perform this action"
            )
        access_token, refresh_token = create_tokens(
            data={"sub": user.username, "scopes": data.scopes},
        )
        _ = update_user_login(user, db)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.post("/refresh/", response_model=Token, response_model_exclude_none=True)
def refresh(token_data: TokenRefreshData, db: Annotated[Session, Depends(get_db)]):
    try:
        access_token = create_access_token(token_data.refresh_token, db)
        return Token(
            access_token=access_token,
            token_type="Bearer",
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Given token is invalid")
    except Exception:
        raise HTTPException(status_code=401, detail="User is not authenticated")


@auth_router.get(
    "/me/", response_model=UserFetchSchema, dependencies=[Depends(get_current_user)]
)
def get_authenticate_user(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user_instance = get_user_by_id(user.id, db)
        user = UserFetchSchema.model_validate(user_instance)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


@auth_router.get(
    "/admin/me/",
    response_model=UserFetchSchema,
    dependencies=[Depends(get_current_user)],
)
def get_admin_authenticated_user(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user_instance = get_user_by_id(user.id, db)
        if not user.is_admin and not user.is_superuser:
            raise HTTPException(
                status_code=403, detail="User is not authorized to perform this action"
            )
        user = UserFetchSchema.model_validate(user_instance)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
