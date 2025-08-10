from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str


class TokenRefreshData(BaseModel):
    refresh_token: str = None


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


class Login(BaseModel):
    username: str
    password: str
