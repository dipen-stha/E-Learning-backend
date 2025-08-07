from sqlmodel import Field, Relationship, SQLModel

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

    categories: list[Category] = Relationship(
        back_populates="courses", link_model=CategoryCourseLink
    )
    subjects: list["Subject"] = Relationship(back_populates="course")
    user_courses: list["UserCourse"] = Relationship(back_populates="course")

    __tablename__ = "courses"


class Subject(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    completion_time: int = Field(default=0, ge=0)
    course_id: int = Field(foreign_key="courses.id")

    course: Course = Relationship(back_populates="subjects")
    units: list["Unit"] = Relationship(back_populates="subject")
    user_subjects: list["UserSubject"] = Relationship(back_populates="subject")

    __tablename__ = "subjects"


class Unit(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    subject_id: int = Field(foreign_key="subjects.id")

    subject: Subject = Relationship(back_populates="units")
    unit_contents: list["UnitContents"] = Relationship(back_populates="unit")
    user_units: list["UserUnit"] = Relationship(back_populates="unit")

    __tablename__ = "units"


class UnitContents(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    unit_id: int = Field(foreign_key="units.id")
    completion_time: int = Field(default=0, ge=0)

    unit: Unit = Relationship(back_populates="unit_contents")
    contents: list["Contents"] = Relationship(back_populates="unit_content")

    __tablename__ = "unit_contents"


class Contents(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    description: str | None
    file_url: str
    unit_content_id: int = Field(foreign_key="unit_contents.id")

    unit_content: UnitContents = Relationship(back_populates="contents")
    user_contents: list["UserContent"] = Relationship(back_populates="content")

    __tablename__ = "contents"
