from sqlmodel import Field, Relationship, SQLModel

from app.db.models.common import UserCourse
from app.db.models.enrollment import CourseEnrollment
from app.services.enum.courses import ContentTypeEnum, LevelEnum, StatusEnum
from app.services.mixins.db_mixins import BaseTimeStampMixin


class CategoryCourseLink(SQLModel, table=True):
    course_id: int = Field(foreign_key="courses.id", primary_key=True)
    category_id: int = Field(foreign_key="categories.id", primary_key=True)

    __tablename__ = "category_course_links"


class Category(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)

    courses: list["Course"] = Relationship(
        back_populates="categories", link_model=CategoryCourseLink
    )

    __tablename__ = "categories"


class Course(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255)
    price: float | None = Field(nullable=True, ge=0)
    completion_time: int | None = Field(nullable=True, ge=0)
    instructor_id: int | None = Field(foreign_key="users.id", nullable=True, index=True)
    image_url: str | None = Field(nullable=True)
    description: str | None
    requirements: str | None
    objectives: str | None
    level: LevelEnum | None = Field(nullable=True)
    status: StatusEnum | None = Field(nullable=True)

    categories: list[Category] = Relationship(
        back_populates="courses", link_model=CategoryCourseLink
    )
    instructor: "User" = Relationship(back_populates="courses_taught")
    subjects: list["Subject"] = Relationship(back_populates="course")
    # users: list["User"] = Relationship(back_populates="user_courses", link_model=UserCourse)
    user_course_links: list["UserCourse"] = Relationship(back_populates="course")
    ratings: list["CourseRating"] = Relationship(back_populates="rated_course")
    user_enrollments: list["CourseEnrollment"] = Relationship(back_populates="course")

    __tablename__ = "courses"


class Subject(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255)
    completion_time: int = Field(default=0, ge=0)
    course_id: int = Field(foreign_key="courses.id", index=True)
    order: int | None = Field(ge=0, nullable=True)
    status: StatusEnum | None = Field(nullable=True)
    description: str | None
    objectives: str | None

    course: Course = Relationship(back_populates="subjects")
    units: list["Unit"] = Relationship(back_populates="subject")
    subject_assessments: list["Assessment"] = Relationship(back_populates="subject")
    # users: list["User"] = Relationship(back_populates="user_subjects", link_model=UserSubject)

    __tablename__ = "subjects"


class Unit(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255)
    completion_time: int | None = Field(nullable=True, ge=0)
    subject_id: int = Field(foreign_key="subjects.id", index=True)
    order: int | None = Field(ge=0, nullable=True)
    status: StatusEnum | None = Field(nullable=True)
    description: str | None
    objectives: str | None

    subject: Subject = Relationship(back_populates="units")
    contents: list["Contents"] = Relationship(back_populates="unit")
    # users: list["User"] = Relationship(back_populates="user_units", link_model=UserUnit)
    user_unit_links: list["UserUnit"] = Relationship(back_populates="unit")

    __tablename__ = "units"


class UnitContents(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255)
    unit_id: int = Field(foreign_key="units.id", index=True)
    completion_time: int = Field(default=0, ge=0)
    order: int | None = Field(ge=0, nullable=True)

    # unit: Unit = Relationship(back_populates="unit_contents")
    # contents: list["Contents"] = Relationship(back_populates="unit_content")

    __tablename__ = "unit_contents"


class Contents(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255)
    description: str | None
    file_url: str | None
    content_type: ContentTypeEnum = Field(default=ContentTypeEnum.TEXT)
    completion_time: int = Field(default=0, ge=0)
    unit_id: int | None = Field(foreign_key="units.id", nullable=True)
    order: int | None = Field(ge=0, nullable=True)
    status: StatusEnum | None = Field(nullable=True, default=StatusEnum.DRAFT)
    unit: Unit = Relationship(back_populates="contents")
    # unit_content: UnitContents = Relationship(back_populates="contents")
    video_time_stamps: list["ContentVideoTimeStamp"] = Relationship(
        back_populates="content"
    )
    user_content_links: list["UserContent"] = Relationship(back_populates="content")
    # users: list["User"] = Relationship(back_populates="user_contents", link_model=UserContent)

    __tablename__ = "contents"


class ContentVideoTimeStamp(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255)
    content_id: int = Field(foreign_key="contents.id", nullable=True)
    time_stamp: int = Field(nullable=True)

    content: Contents = Relationship(back_populates="video_time_stamps")

    __tablename__ = "video_time_stamps"


class CourseRating(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    rating: int = Field(ge=0)
    remarks: str | None

    rated_by: "User" = Relationship(back_populates="user_ratings")
    rated_course: Course = Relationship(back_populates="ratings")

    __tablename__ = "course_ratings"
