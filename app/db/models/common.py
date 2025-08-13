from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship

from app.services.enum.courses import CompletionStatusEnum
from app.services.mixins.db_mixins import BaseTimeStampMixin


class UserCourse(SQLModel, BaseTimeStampMixin, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True, index=True)
    course_id: int = Field(foreign_key="courses.id", primary_key=True, index=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.IN_PROGRESS, index=True)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(nullable=True)

    user: "User" = Relationship(back_populates="user_course_links")
    course: "Course" = Relationship(back_populates="user_course_links")

    __tablename__ = "user_courses"


class UserContent(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True, index=True)
    content_id: int = Field(foreign_key="contents.id", primary_key=True, index=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.IN_PROGRESS, index=True)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(nullable=True)

    __tablename__ = "user_contents"


class UserUnit(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True, index=True)
    unit_id: int = Field(foreign_key="units.id", primary_key=True, index=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.NOT_STARTED, index=True)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(nullable=True)

    __tablename__ = "user_units"


class UserSubject(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True, index=True)
    subject_id: int = Field(foreign_key="subjects.id", primary_key=True, index=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.NOT_STARTED, index=True)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(nullable=True)
