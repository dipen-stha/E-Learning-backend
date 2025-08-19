from pydantic import BaseModel, Field

from app.api.v1.schemas.users import ProfileSchema
from app.db.models.courses import Contents, Subject, Unit, UnitContents
from app.services.enum.courses import ContentTypeEnum


class Base(BaseModel):
    title: str


class CategoryFetch(Base):
    id: int

    class Config:
        from_attributes = True


class CourseUpdate(BaseModel):
    title: str | None = None
    categories_id: list[int] | None = None
    instructor_id: int | None = None


class CourseCreate(Base):
    categories_id: list[int] or [] = []
    price: float = Field(ge=0)
    completion_time: int = Field(ge=0)
    instructor_id: int


class BaseCourse(Base):
    id: int
    title: str

    class Config:
        from_attributes = True


class CourseFetch(BaseCourse):
    id: int
    title: str
    price: float
    description: str | None = None
    completion_time: int
    instructor: ProfileSchema | None = None
    image_url: str | None


class CourseDetailFetch(CourseFetch):
    student_count: int | None
    course_rating: float | None
    categories: list[str]
    subjects: list["SubjectFetch"] = []


class SubjectCreate(Base):
    completion_time: int
    course_id: int
    order: int


class BaseSubjectFetch(Base):
    id: int

    class Config:
        from_attributes = True


class SubjectDetailsFetch(BaseModel):
    id: int
    title: str
    total_units: int | None = Field(ge=0)
    completion_time: int
    completed_units: int | None = None
    units: list["UnitFetchBase"]
    progress: int | None = None


class SubjectFetch(BaseSubjectFetch):
    completion_time: int = Field(default=0, ge=0)
    course: BaseCourse | None = None
    order: int | None
    units: list[str] | list["UserUnitDetail"] = []
    total_units: int | None = None
    completed_units: int | None = None
    completion_percent: float | None = None

    @staticmethod
    def from_orm(subject: Subject):
        return SubjectFetch(
            id=subject.id,
            title=subject.title,
            completion_time=subject.completion_time,
            course=BaseCourse.model_validate(subject.course),
            order=subject.order,
        )


class UnitFetchBase(BaseModel):
    id: int
    title: str
    is_completed: bool


class UnitCreate(Base):
    subject_id: int
    order: int


class BaseUnit(Base):
    id: int

    class Config:
        from_attributes = True


class UnitFetch(BaseUnit):
    id: int
    subject: BaseSubjectFetch | None
    order: int | None

    @staticmethod
    def from_orm(unit: Unit):
        return UnitFetch(
            id=unit.id,
            title=unit.title,
            subject=BaseSubjectFetch.model_validate(unit.subject),
            order=unit.order,
        )


class UserUnitDetail(Base):
    id: int
    is_completed: bool = False


class UnitUpdate(BaseModel):
    title: str | None = None
    subject_id: int | None = None
    order: int | None = None


class BaseUnitContent(Base):
    id: int
    title: str

    class Config:
        from_attributes = True


class UnitContentCreate(Base):
    unit_id: int
    completion_time: int = Field(default=None, ge=0)
    order: int


class UnitContentFetch(BaseUnitContent):
    completion_time: int
    course: BaseCourse
    order: int | None

    @classmethod
    def from_orm(unit_content: UnitContents):
        return UnitContentFetch(
            id=unit_content.id,
            title=unit_content.title,
            completion_time=unit_content.completion_time,
            course=BaseCourse.model_validate(unit_content.course),
            order=unit_content.order,
        )


class UnitContentUpdate(BaseModel):
    title: str | None = None
    completion_time: int | None = Field(default=None, ge=0)
    unit_id: int | None = None
    order: int | None = None


class BaseContent(Base):
    id: int


class ContentCreate(Base):
    completion_time: int = Field(default=None, ge=0)
    order: int
    description: str | None
    content_type: ContentTypeEnum


class ContentFetch(BaseContent):
    completion_time: int
    order: int | None
    description: str | None = None
    content_type: ContentTypeEnum
    file_url: str | None = None

    class Config:
        from_attributes = True


class ContentUpdate(BaseModel):
    completion_time: int | None = None
    unit_id: int | None = None
    title: str | None = None
    order: int | None = None
