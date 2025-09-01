from pydantic import BaseModel, Field

from app.api.v1.schemas.users import ProfileSchema, MinimalUserFetch
from app.services.enum.courses import ContentTypeEnum, StatusEnum


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
    description: str | None
    requirements: str | None
    objectives: str | None
    instructor_id: int
    status: StatusEnum


class BaseCourse(Base):
    id: int
    title: str

    class Config:
        from_attributes = True


class CourseFetch(BaseCourse):
    id: int
    title: str
    price: float | None = None
    description: str | None = None
    completion_time: int
    instructor: ProfileSchema | str | None = None
    image_url: str | None


class LatestCourseFetch(BaseModel):
    id: int
    title: str
    completion_time: int
    price: float
    instructor_name: str
    image_url: str | None
    student_count: int | None
    course_rating: int | None


class CourseDetailFetch(CourseFetch):
    student_count: int | None
    course_rating: float | None
    categories: list[str] = []
    subjects: list["SubjectFetch"] | list[str] = []
    total_revenue: float | None = None
    status: StatusEnum
    is_enrolled: bool = Field(default=False)


class SubjectCreate(Base):
    completion_time: int
    course_id: int
    order: int
    status: StatusEnum
    description: str | None = None
    objectives: str | None = None


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
    completion_time: int | None = None
    course: BaseCourse | None = None
    instructor: ProfileSchema | None = None
    order: int | None = None
    units: list[str] | list["UserUnitDetail"] = []
    total_units: int | None = None
    completed_units: int | None = None
    completion_percent: float | None = None
    description: str | None = None
    status: StatusEnum | None = None
    student_count: int | None = None


class DetailedSubjectFetch(BaseModel):
    id: int
    title: str
    course_title: str
    completion_percent: int
    total_units: int
    completed_units: int
    completion_time: int
    units: list["UnitWithContents"]


class UnitFetchBase(BaseModel):
    id: int
    title: str
    is_completed: bool


class UnitCreate(Base):
    subject_id: int
    order: int
    completion_time: int
    description: str | None = None
    status: StatusEnum
    objectives: str | None = None
    order: int


class BaseUnit(Base):
    id: int

    class Config:
        from_attributes = True


class UnitWithContents(BaseModel):
    id: int
    title: str
    completion_time: int
    contents: list["ContentFetch"]
    is_started: bool = False


class UnitFetch(BaseUnit):
    id: int
    subject: BaseSubjectFetch | str | None = None
    order: int | None
    completion_time: int
    course: str | None = None
    status: StatusEnum
    description: str | None
    objectives: str | None


class UserUnitDetail(Base):
    id: int
    is_completed: bool = False


class UnitUpdate(BaseModel):
    title: str | None = None
    subject_id: int | None = None
    order: int | None = None


class BaseContent(Base):
    id: int


class VideoTimeStamp(BaseModel):
    title: str
    time_stamp: int


class ContentCreate(Base):
    completion_time: int = Field(ge=0)
    order: int
    description: str | None
    content_type: ContentTypeEnum
    status: StatusEnum
    video_time_stamps: list[VideoTimeStamp] = []
    unit_id: int


class ContentFetch(BaseContent):
    completion_time: int
    order: int | None
    description: str | None = None
    content_type: ContentTypeEnum
    file_url: str | None = None
    course: str | None = None
    instructor: ProfileSchema | None = None
    status: StatusEnum
    video_time_stamps: list["VideoTimeStamps"] = []

    class Config:
        from_attributes = True


class VideoTimeStamps(BaseModel):
    id: int
    title: str
    time_stamp: int


class ContentUpdate(BaseModel):
    completion_time: int | None = None
    unit_id: int | None = None
    title: str | None = None
    order: int | None = None


class SubjectDetailedFetch(BaseModel):
    id: int
    title: str
    course: BaseCourse
    completion_time: int
    units: list[UnitWithContents]
