from datetime import datetime

from pydantic import BaseModel, Field, field_validator, field_serializer
from sqlalchemy.exc import NoResultFound

from app.api.v1.schemas.courses import BaseContent, BaseUnit
from app.api.v1.schemas.users import UserFetchSchema
from app.api.v1.schemas.courses import BaseCourse, BaseSubjectFetch
from app.db.models.courses import Course, Contents, Unit, Subject
from app.db.models.users import User
from app.services.enum.courses import CompletionStatusEnum
from app.services.utils.crud_utils import get_model_instance_by_id


class BaseCommonSchema(BaseModel):
    user_id: int
    expected_completion_time: int = Field(ge=0)
    status: CompletionStatusEnum = Field(default=CompletionStatusEnum.IN_PROGRESS)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    @field_validator("user_id", mode="after")
    @classmethod
    def validate_user_id(cls, value):
        if not get_model_instance_by_id(User, value):
            raise NoResultFound(f"User with id {value} not found")
        return value


class BaseCommonFetch(BaseModel):
    user_name: str | None
    expected_completion_time: int
    status: CompletionStatusEnum
    started_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class BaseCommonUpdate(BaseModel):
    status: CompletionStatusEnum | None


class UserCourseCreate(BaseCommonSchema):
    course_id: int

    @field_validator("course_id", mode="after")
    @classmethod
    def validate_course_id(cls, value):
        if not get_model_instance_by_id(Course, value):
            raise NoResultFound(f"Course with id {value} not found")
        return value


class UserCourseFetch(BaseCommonFetch):
    course: BaseCourse
    next_subject: str | None = None

    completion_percent: float | None = None

    total_subjects: int | None = None
    completed_subjects: int | None = None

    class Config:
        from_attributes = True


class UserCourseStats(BaseModel):
    courses_enrolled: int
    completed_courses: int

class UserContentCreate(BaseCommonSchema):
    content_id: int

    @field_validator("content_id", mode="after")
    @classmethod
    def validate_content_id(cls, value):
        if not get_model_instance_by_id(Contents, value):
            raise NoResultFound(f"Content with id {value} not found")
        return value


class UserContentFetch(BaseCommonFetch):
    content: BaseContent

    class Config:
        from_attributes = True


class UserUnitCreate(BaseCommonSchema):
    unit_id: int

    @field_validator("unit_id", mode="after")
    @classmethod
    def validate_unit_id(cls, value):
        if not get_model_instance_by_id(Unit, value):
            raise NoResultFound(f"Unit with id {value} not found")
        return value


class UserUnitFetch(BaseCommonFetch):
    unit: BaseUnit
    completion_percent: float | None

    class Config:
        from_attributes = True


class UserSubjectCreate(BaseCommonSchema):
    subject_id: int

    @field_validator("subject_id", mode="after")
    @classmethod
    def validate_subject_id(cls, value):
        if not get_model_instance_by_id(Subject, value):
            raise NoResultFound(f"Subject with id {value} not found")
        return value


class UserSubjectFetch(BaseCommonFetch):
    subject: BaseSubjectFetch
    completion_percent: float | None

    class Config:
        from_attributes = True
