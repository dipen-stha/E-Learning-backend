from datetime import date

from pydantic import BaseModel

from app.db.models.users import User
from app.services.enum.users import UserGender


class UserCreateSchema(BaseModel):
    email: str
    username: str
    password: str
    name: str
    gender: UserGender
    dob: date


class ProfileSchema(BaseModel):
    name: str
    dob: date
    gender: UserGender
    avatar: str | None = None

    class Config:
        from_attributes = True


class UserFetchSchema(BaseModel):
    id: int | None
    profile: ProfileSchema | None
    email: str
    username: str

    @staticmethod
    def from_orm(user: User) -> "UserFetchSchema":
        return UserFetchSchema(
            id=user.id,
            profile=ProfileSchema.model_validate(user.profile),
            email=user.email,
            username=user.username,
        )

    class Config:
        from_attributes = True
