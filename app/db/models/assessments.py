from sqlmodel import SQLModel, Field, Relationship

from app.services.enum.courses import PaymentMethod
from app.services.mixins.db_mixins import BaseTimeStampMixin


# class UserCourseEnrollment(SQLModel, BaseTimeStampMixin, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     course_id: int = Field(foreign_key="courses.id")
#     user_id: int = Field(foreign_key="users.id")
#     is_paid: bool = Field(default=False)
#
#     payment_method: PaymentMethod | None = Field(nullable=True)
#     total_amount_paid: float | None = Field(nullable=True, ge=0)
#
#     user: "User" = Relationship()
#     course: "Course" = Relationship()
#
#     __tablename__ = "user_course_enrollments"
