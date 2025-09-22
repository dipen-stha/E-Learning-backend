from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from sqlmodel import Session, and_, asc, case, select

from app.api.v1.schemas.courses import CourseFetch, SubjectFetch, UserUnitDetail
from app.api.v1.schemas.enrollment import (
    CourseEnrollmentCreate,
    CourseEnrollmentUpdate,
    UserCourseEnrollment,
)
from app.db.crud.common import get_subject_detail_with_unit_counts
from app.db.models.common import UserCourse, UserSubject
from app.db.models.courses import Course, Subject
from app.db.models.enrollment import CourseEnrollment
from app.db.models.users import User
from app.services.enum.courses import CompletionStatusEnum, PaymentStatus
from app.services.utils.crud_utils import update_model_instance
from app.services.utils.files import format_file_path


def course_enrollment_create(
    enrollment_data: CourseEnrollmentCreate,
    provider_payment_id: str,
    metadata: dict,
    db: Session,
) -> CourseEnrollment:
    data = enrollment_data.model_dump()
    course_enrollment = CourseEnrollment(
        provider_payment_id=provider_payment_id, metadata=metadata, **data
    )
    db.add(course_enrollment)
    db.commit()
    db.refresh(course_enrollment)
    return course_enrollment


def course_enrollment_payment_update(
    enrollment_id: int, enrollment_data: CourseEnrollmentUpdate, db: Session
) -> CourseEnrollment:
    data = enrollment_data.model_dump()
    enrollment_instance = db.exec(
        select(CourseEnrollment).where(
            CourseEnrollment.provider_payment_id == enrollment_id
        )
    ).first()
    if not enrollment_instance:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    updated_instance = update_model_instance(enrollment_instance, data)
    db.add(updated_instance)
    db.commit()
    db.refresh(updated_instance)
    print(data.get("status"))
    return updated_instance


def fetch_user_enrollments(user_id: int, db: Session):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with pk {user_id} not found")
    # subject_statement = (
    #     select(Subject.id, Subject.title)
    #     .join(
    #         UserSubject,
    #         and_(UserSubject.subject_id == Subject.id, UserSubject.user_id == user_id),
    #         isouter=True,
    #     )
    #     .where(
    #         Subject.course_id == Course.id,
    #         Subject.order is not None,
    #     )
    #     .order_by(asc(Subject.order))
    #     .limit(1)
    #     .correlate(Course)
    #     .subquery()
    # )
    statement = (
        select(
            CourseEnrollment,
            # subject_statement.c.id, subject_statement.c.title,
            func.count(Subject.id).label("subject_counts"),
            func.count(UserSubject.subject_id)
            .filter(UserSubject.status == CompletionStatusEnum.COMPLETED)
            .label("completed_counts"),
            case(
                (UserCourse.status == CompletionStatusEnum.COMPLETED, True), else_=False
            ).label("is_completed"),
            case(
                (UserCourse.status == CompletionStatusEnum.IN_PROGRESS, True),
                else_=False,
            ).label("is_started"),
        )
        .select_from(CourseEnrollment)
        .join(Course, CourseEnrollment.course_id == Course.id)
        .join(UserCourse, UserCourse.course_id == Course.id, isouter=True)
        .join(Subject, Subject.course_id == Course.id)
        .outerjoin(UserSubject)
        .where(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.status == PaymentStatus.PAID,
        )
        .group_by(CourseEnrollment.id, UserCourse.status)
    )
    user_enrollments = db.exec(statement).all()
    return [
        UserCourseEnrollment(
            course=CourseFetch(
                id=course_enrollment.course.id,
                title=course_enrollment.course.title,
                completion_time=course_enrollment.course.completion_time,
                image_url=format_file_path(course_enrollment.course.image_url),
            ),
            instructor=course_enrollment.course.instructor.profile.name,
            total_subjects=total_subjects,
            completed_subjects=completed_subjects,
            completion_percent=(
                round(completed_subjects / total_subjects * 100, 2)
                if (completed_subjects and total_subjects)
                else 0
            ),
            is_completed=is_completed,
            is_started=is_started,
        )
        for course_enrollment, total_subjects, completed_subjects, is_completed, is_started in user_enrollments
    ]


def fetch_user_enrollments_by_course(user_id: int, course_id: int, db: Session):
    course = db.get(Course, course_id)
    if not course:
        raise NoResultFound(f"Course with pk {course_id} not found")
    user_course = db.exec(
        select(UserCourse).where(
            UserCourse.course_id == course.id, UserCourse.user_id == user_id
        )
    ).first()
    subject_details = {
        subject.id: subject
        for subject in get_subject_detail_with_unit_counts(course_id, user_id, db)
    }
    subject_subquery = (
        select(Subject.title)
        .join(
            UserSubject,
            and_(UserSubject.subject_id == Subject.id, UserSubject.user_id == user_id),
            isouter=True,
        )
        .where(Subject.order is not None, Subject.course_id == course_id)
        .order_by(asc(Subject.order))
        .limit(1)
        .scalar_subquery()
    )
    statement = (
        select(
            CourseEnrollment,
            func.count(Subject.id).label("total_subjects"),
            func.count(Subject.id)
            .filter(UserSubject.status == CompletionStatusEnum.COMPLETED)
            .label("completed_counts"),
            subject_subquery.label("next_subject"),
        )
        .join(Course, Course.id == CourseEnrollment.course_id)
        .join(Subject, Subject.course_id == course_id)
        .outerjoin(UserSubject, Subject.id == UserSubject.subject_id)
        .options(
            selectinload(CourseEnrollment.user).selectinload(User.profile),
            selectinload(CourseEnrollment.course)
            .selectinload(Course.subjects)
            .selectinload(Subject.units),
        )
        .where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.status == PaymentStatus.PAID,
        )
        .group_by(CourseEnrollment.id)
    )
    enrollment = db.exec(statement).first()
    if not enrollment:
        return None
    course_enrollment, total_subjects, completed_subjects, next_subject = enrollment
    return UserCourseEnrollment(
        course=course_enrollment.course,
        next_subject=next_subject,
        total_subjects=total_subjects,
        completed_subjects=completed_subjects,
        is_started=bool(user_course),
        is_completed=(
            True
            if (user_course and user_course.status == CompletionStatusEnum.COMPLETED)
            else False
        ),
        subjects=[
            SubjectFetch(
                id=subject.id,
                title=subject.title,
                completion_time=subject.completion_time,
                order=subject.order,
                units=[
                    UserUnitDetail(
                        id=unit.id,
                        title=unit.title,
                        # is_completed=subject_details.get(subject.id).is_completed,
                    )
                    for unit in subject.units
                ],
                total_units=(
                    subject_details.get(subject.id).total_units
                    if subject_details.get(subject.id)
                    else 0
                ),
                completed_units=(
                    subject_details.get(subject.id).completed_units
                    if subject_details.get(subject.id)
                    else 0
                ),
                completion_percent=(
                    (
                        subject_details.get(subject.id).completed_units
                        / subject_details.get(subject.id).total_units
                    )
                    * 100
                    if (
                        subject_details.get(subject.id)
                        and subject_details.get(subject.id).completed_units
                        and subject_details.get(subject.id).total_units
                    )
                    else 0
                ),
            )
            for subject in course_enrollment.course.subjects
        ],
    )
