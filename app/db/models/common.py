from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship

from app.db.models.courses import Course
from app.services.enum.courses import CompletionStatusEnum
from app.services.mixins.db_mixins import BaseTimeStampMixin


class UserCourse(SQLModel, BaseTimeStampMixin, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    course_id: int = Field(foreign_key="courses.id", primary_key=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.IN_PROGRESS)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(nullable=True)

    user: "User" = Relationship()
    course: Course = Relationship(back_populates="user_courses")

    __tablename__ = "user_courses"


class UserContent(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    content_id: int = Field(foreign_key="contents.id", primary_key=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.IN_PROGRESS)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(nullable=True)

    content: "Contents" = Relationship(back_populates="user_contents")

    __tablename__ = "user_contents"


class UserUnit(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    unit_id: int = Field(foreign_key="units.id", primary_key=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.NOT_STARTED)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(nullable=True)

    unit: "Unit" = Relationship(back_populates="user_units")

    __tablename__ = "user_units"


class UserSubject(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    subject_id: int = Field(foreign_key="subjects.id", primary_key=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.NOT_STARTED)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(nullable=True)

    subject: "Subject" = Relationship(back_populates="user_subjects")
