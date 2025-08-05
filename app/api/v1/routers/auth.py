from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.api.v1.schemas.auth import Token, Login, TokenData
from app.db.session.session import get_db
from app.services.auth.core import authenticate_user, create_tokens

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/login/", response_model=Token)
def login(data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(get_db)]):
    try:
        user, _ = authenticate_user(data.username, data.password, db)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
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
