from fastapi import HTTPException
from sqlmodel import select, Session

from app.db.models.enrollment import CourseEnrollment
from app.api.v1.schemas.enrollment import CourseEnrollmentCreate, CourseEnrollmentFetch, CourseEnrollmentUpdate
from app.services.utils.crud_utils import update_model_instance


def course_enrollment_create(enrollment_data: CourseEnrollmentCreate, provider_payment_id: str, metadata:dict, db: Session) -> CourseEnrollment:
    data = enrollment_data.model_dump()
    course_enrollment = CourseEnrollment(provider_payment_id=provider_payment_id, metadata=metadata, **data)
    db.add(course_enrollment)
    db.commit()
    db.refresh(course_enrollment)
    return course_enrollment

def course_enrollment_payment_update(enrollment_id: int, enrollment_data: CourseEnrollmentUpdate, db: Session) -> CourseEnrollment:
    data = enrollment_data.model_dump()
    enrollment_instance = db.exec(select(CourseEnrollment).where(CourseEnrollment.provider_payment_id == enrollment_id)).first()
    if not enrollment_instance:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    updated_instance = update_model_instance(enrollment_instance, data)
    db.add(updated_instance)
    db.commit()
    db.refresh(updated_instance)
    print(data.get("status"))
    return updated_instance