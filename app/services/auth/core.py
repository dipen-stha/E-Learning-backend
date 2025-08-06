from datetime import datetime, timedelta
from typing import Annotated

import jwt
from jwt import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.api.v1.schemas.auth import TokenData
from app.db.crud.users import get_user_by_username
from app.db.models.users import User
from app.services.auth.hash import verify_password
from config import settings

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 1

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"me": "Read information about the current user", "items": "Read items"},
)


def authenticate_user(username: str, password: str, db: Session) -> (User, bool):
    user = get_user_by_username(username, db)
    if not user:
        return None, False
    if not verify_password(password, user.password):
        return None, False
    return user, True


def create_tokens(data: dict) -> (str, str):
    to_encode = data.copy()
    access_expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": access_expire, "type": "access"})
    access_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    to_encode.update({"exp": refresh_expire, "type": "refresh"})
    refresh_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return access_jwt, refresh_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session,
):
    if security_scopes.scopes:
        authenticate_value = f"Bearer scope={security_scopes.scope_str}"
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception
    user, _ = get_user_by_username(username, db)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["me"])],
):
    if current_user[0].is_active:
        return current_user
    raise HTTPException(status_code=400, detail="Inactive user")
