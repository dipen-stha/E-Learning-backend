from datetime import date

from sqlmodel import Field, Relationship, SQLModel

from app.db.models.common import UserCourse, UserContent, UserSubject, UserUnit
from app.db.models.gamification import UserStreak, UserAchievements
from app.db.models.courses import Course
from app.services.enum.users import UserGender, UserRole
from app.services.mixins.db_mixins import BaseTimeStampMixin


class User(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    username: str = Field(max_length=255, unique=True, index=True)
    password: str = Field(max_length=255)
    email: str = Field(max_length=255)
    profile: "Profile" or None = Relationship(
        back_populates="user", sa_relationship_kwargs={"uselist": False}
    )
    is_superuser: bool = Field(default=False)
    is_active: bool = Field(default=True, index=True)

    # user_courses: list["Course"] = Relationship(back_populates="users", link_model=UserCourse)
    # user_units: list["Unit"] = Relationship(back_populates="users", link_model=UserUnit)
    # user_subjects: list["Subject"] = Relationship(back_populates="users", link_model=UserSubject)
    # user_contents: list["Contents"] = Relationship(back_populates="users", link_model=UserContent)

    courses_taught: list[Course] = Relationship(back_populates="instructor")
    user_course_links: list[UserCourse] = Relationship(back_populates="user")
    user_ratings: list["CourseRating"] = Relationship(back_populates="rated_by")
    achieved: list[UserAchievements] = Relationship(back_populates="achieved_by")
    users_streaks: list[UserStreak] = Relationship(back_populates="streak_by")

    __tablename__ = "users"


class Profile(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    name: str = Field(max_length=255)
    user: User = Relationship(back_populates="profile")
    gender: UserGender | None = Field(default=None, nullable=True)
    dob: date | None = Field(nullable=True)
    role: UserRole = Field(default=UserRole.STUDENT)
    avatar: str | None = Field(nullable=True)

    __tablename__ = "profiles"
