from datetime import datetime

from sqlmodel import Field, SQLModel

from app.services.enum.courses import CompletionStatusEnum
from app.services.mixins.db_mixins import BaseTimeStampMixin


class UserCourse(SQLModel, BaseTimeStampMixin, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    course_id: int = Field(foreign_key="courses.id", primary_key=True)
    expected_course_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.IN_PROGRESS)
    started_at: datetime = Field(default=datetime.now)
    completed_at: datetime = Field(nullable=True)

    __tablename__ = "user_courses"


class UserContent(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    content_id: int = Field(foreign_key="contents.id", primary_key=True)
    expected_content_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.IN_PROGRESS)
    started_at: datetime = Field(default=datetime.now)
    completed_at: datetime = Field(nullable=True)

    __tablename__ = "user_contents"


class UserUnit(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    unit_id: int = Field(foreign_key="units.id", primary_key=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.NOT_STARTED)
    started_at: datetime = Field(default=datetime.now)
    completed_at: datetime = Field(nullable=True)

    __tablename__ = "user_units"


class UserSubject(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    subject_id: int = Field(foreign_key="subjects.id", primary_key=True)
    expected_completion_time: int = Field(default=0, ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.NOT_STARTED)
    started_at: datetime = Field(default=datetime.now)
    completed_at: datetime = Field(nullable=True)
