from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from app.services.enum.courses import PaymentMethod, PaymentStatus
from app.services.mixins.db_mixins import BaseTimeStampMixin


class CourseEnrollment(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, nullable=False, primary_key=True)
    user_id: int | None = Field(foreign_key="users.id", index=True)
    course_id: int | None = Field(foreign_key="courses.id", index=True)
    provider: PaymentMethod = Field(default=PaymentMethod.STRIPE, index=True)
    provider_payment_id: str | None = Field(default=None, nullable=True, index=True)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, index=True)
    amount: int | None = Field(default=None, nullable=True)
    currency: str = Field(default="USD", index=True)

    failure_code: str | None = Field(default=None, nullable=True)
    failure_message: str | None = Field(default=None, nullable=True)

    provider_metadata: dict | None = Field(sa_column=Column(JSON))

    user: "User" = Relationship(back_populates="course_enrollments")
    course: "Course" = Relationship(back_populates="user_enrollments")

    __tablename__ = "course_enrollments"
