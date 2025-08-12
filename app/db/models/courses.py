from sqlmodel import Field, Relationship, SQLModel

from app.db.models.common import UserCourse, UserSubject, UserUnit, UserContent
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
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    price: float | None = Field(nullable=True, ge=0)
    completion_time: int | None = Field(nullable=True, ge=0)

    categories: list[Category] = Relationship(
        back_populates="courses", link_model=CategoryCourseLink
    )
    subjects: list["Subject"] = Relationship(back_populates="course")
    # users: list["User"] = Relationship(back_populates="user_courses", link_model=UserCourse)
    user_course_links: list["UserCourse"] = Relationship(back_populates="course")
    ratings: list["CourseRating"] = Relationship(back_populates="rated_course")

    __tablename__ = "courses"


class Subject(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    completion_time: int = Field(default=0, ge=0)
    course_id: int = Field(foreign_key="courses.id")
    order: int | None = Field(ge=0, nullable=True)

    course: Course = Relationship(back_populates="subjects")
    units: list["Unit"] = Relationship(back_populates="subject")
    # users: list["User"] = Relationship(back_populates="user_subjects", link_model=UserSubject)

    __tablename__ = "subjects"


class Unit(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    completion_time: int | None = Field(nullable=True, ge=0)
    subject_id: int = Field(foreign_key="subjects.id")
    order: int | None = Field(ge=0, nullable=True)

    subject: Subject = Relationship(back_populates="units")
    unit_contents: list["UnitContents"] = Relationship(back_populates="unit")
    # users: list["User"] = Relationship(back_populates="user_units", link_model=UserUnit)

    __tablename__ = "units"


class UnitContents(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    unit_id: int = Field(foreign_key="units.id")
    completion_time: int = Field(default=0, ge=0)
    order: int | None = Field(ge=0, nullable=True)

    unit: Unit = Relationship(back_populates="unit_contents")
    contents: list["Contents"] = Relationship(back_populates="unit_content")

    __tablename__ = "unit_contents"


class Contents(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    description: str | None
    file_url: str
    unit_content_id: int = Field(foreign_key="unit_contents.id")
    order: int | None = Field(ge=0, nullable=True)

    unit_content: UnitContents = Relationship(back_populates="contents")
    # users: list["User"] = Relationship(back_populates="user_contents", link_model=UserContent)

    __tablename__ = "contents"


class CourseRating(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id")
    user_id: int = Field(foreign_key="users.id")
    rating: int = Field(ge=0)
    remarks: str | None

    rated_by: "User" = Relationship(back_populates="user_ratings")
    rated_course: Course = Relationship(back_populates="ratings")

    __tablename__ = "course_ratings"