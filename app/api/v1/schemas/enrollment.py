from pydantic import BaseModel

from app.api.v1.schemas.courses import BaseCourse, CourseDetailFetch, SubjectFetch, CourseFetch
from app.api.v1.schemas.users import MinimalUserFetch
from app.services.enum.courses import PaymentMethod, PaymentStatus


class CourseEnrollmentCreate(BaseModel):
    user_id: int
    course_id: int
    provider: PaymentMethod
    status: PaymentStatus
    amount: float
    currency: str = "USD"


class CourseEnrollmentFetch(BaseModel):
    id: int
    user: MinimalUserFetch
    course: BaseCourse
    provider: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    amount: int


class CourseEnrollmentUpdate(BaseModel):
    status: PaymentStatus
    failure_code: str | None = None
    failure_message: str | None = None


class PaymentIntentResponse(BaseModel):
    client_secret: str
    enrollment_id: int


class UserCourseEnrollment(BaseModel):
    course: BaseCourse | CourseFetch
    next_subject: str | None = None
    completion_percent: float | None = None
    total_subjects: int | None = None
    completed_subjects: int | None = None
    is_completed: bool = False
    is_started: bool = False
    subjects: list[SubjectFetch] = []
    instructor: str | None = None