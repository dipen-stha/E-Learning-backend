from pydantic import BaseModel, Field

from app.db.models.courses import Contents, Course, Subject, Unit, UnitContents


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
    categories_id: list[int]
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
    student_count: int | None = Field(ge=0, nullable=True)
    course_rating: float | None = Field(ge=0, nullable=True)
    instructor: str | None
    categories: list[str]
    image_url: str | None

    @staticmethod
    def from_orm(course: Course):
        return CourseFetch(
            id=course.id,
            title=course.title,
            categories=[category.title for category in course.categories],
            price=course.price,
            completion_time=course.completion_time
        )

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
    course: BaseCourse
    order: int | None

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
    unit_id: int
    completion_time: int = Field(default=None, ge=0)
    order: int


class ContentFetch(BaseContent):
    completion_time: int
    unit: BaseUnit
    order: int | None

    class Config:
        from_attributes = True

    @staticmethod
    def from_orm(content: Contents):
        return ContentFetch(
            id=content.id,
            title=content.title,
            unit=BaseUnit.model_validate(content.unit),
            completion_time=content.completion_time,
            order = content.order
        )


class ContentUpdate(BaseModel):
    completion_time: int | None = None
    unit_id: int | None = None
    title: str | None = None
    order: int | None = None
