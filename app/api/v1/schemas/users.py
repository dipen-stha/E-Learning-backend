from datetime import date

from pydantic import BaseModel, model_validator
from pydantic_core import ValidationError

from app.services.enum.users import UserGender, UserRole


class UserCreateSchema(BaseModel):
    email: str
    username: str
    password: str
    confirm_password: str | None = None
    name: str
    gender: UserGender
    dob: date | None = None
    is_active: bool | None = None
    role: UserRole | None = None

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.confirm_password and self.password != self.confirm_password:
            raise ValidationError("Passwords don't match")
        return self


class UserUpdateSchema(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str | None = None
    confirm_password: str | None = None
    name: str | None = None
    gender: UserGender | None = None
    dob: date | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.confirm_password and self.password != self.confirm_password:
            raise ValidationError("Passwords don't match")
        return self


class ProfileSchema(BaseModel):
    id: int | None = None
    name: str
    dob: date | None = None
    gender: UserGender | None = None
    avatar: str | None = None
    role: str | None = None

    class Config:
        from_attributes = True


class UserFetchSchema(BaseModel):
    id: int | None
    profile: ProfileSchema | None
    email: str
    username: str
    is_active: bool | None = None

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


class UserStats(BaseModel):
    total_count: int
    active_count: int
    suspended_count: int
    monthly_creation: int
    percent_total_count: float
    percent_active_count: float
    percent_monthly_creation: float
    percent_suspended_count: float
