from datetime import date

from sqlmodel import Field, Relationship, SQLModel

from app.services.enum.users import UserGender, UserRole
from app.services.mixins.db_mixins import BaseTimeStampMixin


class User(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=255, unique=True)
    password: str = Field(max_length=255)
    email: str = Field(max_length=255)
    profile: "Profile" or None = Relationship(
        back_populates="user", sa_relationship_kwargs={"uselist": False}
    )
    is_superuser: bool = Field(default=False)
    is_active: bool = Field(default=True)

    __tablename__ = "users"


class Profile(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    name: str = Field(max_length=255)
    user: User = Relationship(back_populates="profile")
    gender: UserGender | None = Field(default=None, nullable=True)
    dob: date | None = Field(nullable=True)
    role: UserRole = Field(default=UserRole.STUDENT)

    __tablename__ = "profiles"
