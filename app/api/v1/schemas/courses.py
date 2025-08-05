from pydantic import BaseModel

from app.db.models.courses import Course


class Base(BaseModel):
    title: str


class CategoryFetch(Base):
    id: int


class CourseCreate(Base):
    categories_id: list[int]


# class CourseFetch(Base):
#     id: int
#     categories: list[CategoryFetch]
#
#     @staticmethod
#     def from_orm(course: Course):
#         return CourseFetch(
#             categories=course.categories,
#         )