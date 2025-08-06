from pydantic import BaseModel, Field

from app.db.models.courses import Contents, Course, Subject, Unit, UnitContents


class Base(BaseModel):
    title: str


class CategoryFetch(Base):
    id: int

    class Config:
        from_attributes = True


class CourseCreate(Base):
    categories_id: list[int]


class BaseCourse(Base):
    id: int
    title: str

    class Config:
        from_attributes = True


class CourseFetch(BaseCourse):
    id: int
    title: str
    categories: list[str]

    @staticmethod
    def from_orm(course: Course):
        return CourseFetch(
            id=course.id,
            title=course.title,
            categories=[category.title for category in course.categories],
        )


class SubjectCreate(Base):
    completion_time: int
    course_id: int


class BaseSubjectFetch(Base):
    id: int

    class Config:
        from_attributes = True


class SubjectFetch(BaseSubjectFetch):
    completion_time: int = Field(default=0, ge=0)
    course: BaseCourse

    @staticmethod
    def from_orm(subject: Subject):
        return SubjectFetch(
            id=subject.id,
            title=subject.title,
            completion_time=subject.completion_time,
            course=BaseCourse.model_validate(subject.course),
        )


class UnitCreate(Base):
    subject_id: int


class BaseUnit(Base):
    id: int

    class Config:
        from_attributes = True


class UnitFetch(BaseUnit):
    id: int
    subject: BaseSubjectFetch | None

    @staticmethod
    def from_orm(unit: Unit):
        return UnitFetch(
            id=unit.id,
            title=unit.title,
            subject=BaseSubjectFetch.model_validate(unit.subject),
        )


class UnitUpdate(BaseModel):
    title: str | None = None
    subject_id: int | None = None


class BaseUnitContent(Base):
    id: int
    title: str

    class Config:
        from_attributes = True


class UnitContentCreate(Base):
    unit_id: int
    completion_time: int = Field(default=None, ge=0)


class UnitContentFetch(BaseUnitContent):
    completion_time: int
    course: BaseCourse

    @classmethod
    def from_orm(unit_content: UnitContents):
        return UnitContentFetch(
            id=unit_content.id,
            title=unit_content.title,
            completion_time=unit_content.completion_time,
            course=BaseCourse.model_validate(unit_content.course),
        )


class UnitContentUpdate(BaseModel):
    title: str | None = None
    completion_time: int | None = Field(default=None, ge=0)
    unit_id: int | None = None


class BaseContent(Base):
    id: int


class ContentCreate(Base):
    unit_id: int
    completion_time: int = Field(default=None, ge=0)


class ContentFetch(BaseContent):
    completion_time: int
    unit: BaseUnit

    class Config:
        from_attributes = True

    @staticmethod
    def from_orm(content: Contents):
        return ContentFetch(
            id=content.id,
            title=content.title,
            unit=BaseUnit.model_validate(content.unit),
            completion_time=content.completion_time,
        )


class ContentUpdate(BaseModel):
    completion_time: int | None = None
    unit_id: int | None = None
    title: str | None = None
