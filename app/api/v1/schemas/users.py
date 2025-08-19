from datetime import date, datetime

from psycopg2.errors import InvalidPassword
from pydantic import BaseModel, model_validator
from pydantic_core import ValidationError

from app.db.models.users import User
from app.services.enum.users import UserGender


class UserCreateSchema(BaseModel):
    email: str
    username: str
    password: str
    confirm_password: str | None = None
    name: str
    gender: UserGender
    dob: date | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.confirm_password and self.password != self.confirm_password:
            raise ValidationError("Passwords don't match")
        return self


class ProfileSchema(BaseModel):
    name: str
    dob: date
    gender: UserGender
    avatar: str | None = None
    role: str | None = None

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


class StudentFetchSchema(BaseModel):
    id: int
    profile: ProfileSchema | None
    email: str
    is_active: bool
    joined_date: date
    last_login: str
    total_courses: int
    courses_completed: int


class MinimalUserFetch(BaseModel):
    id: int
    name: str