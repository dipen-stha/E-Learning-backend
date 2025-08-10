from typing import Annotated

from jwt import ExpiredSignatureError, InvalidTokenError
from sqlmodel import Session

from app.api.v1.schemas.auth import Token, TokenRefreshData
from app.db.session.session import get_db
from app.services.auth.core import authenticate_user, create_tokens, create_access_token, get_current_user

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm


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
    except Exception as e:
        raise HTTPException(status_code=401, detail="User is not authenticated")