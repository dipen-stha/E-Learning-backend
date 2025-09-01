from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.types import Integer
from sqlmodel import Session, and_, asc, case, func, select
from sqlmodel.sql import expression

from app.api.v1.schemas.common import (
    BaseCommonUpdate,
    UserContentCreate,
    UserContentFetch,
    UserCourseCreate,
    UserCourseFetch,
    UserCourseStats,
    UserSubjectCreate,
    UserSubjectFetch,
    UserUnitCreate,
    UserUnitFetch, UserSubjectUnitStatus, UserUnitStatus,
)
from app.api.v1.schemas.courses import SubjectFetch, UserUnitDetail, SubjectDetailedFetch, UnitWithContents, \
    ContentFetch
from app.db.models.common import UserContent, UserCourse, UserSubject, UserUnit
from app.db.models.courses import Contents, Course, Subject, Unit, ContentVideoTimeStamp
from app.db.models.users import User
from app.services.enum.courses import CompletionStatusEnum
from app.services.utils.crud_utils import create_model_instance, update_model_instance


def user_course_create(user_course: UserCourseCreate, db: Session) -> UserCourseFetch:
    try:
        data = user_course.model_dump()
        created_user_course_instance = create_model_instance(UserCourse, data, db)
        statement = (
            select(UserCourse)
            .options(
                joinedload(UserCourse.course),
                selectinload(UserCourse.user).selectinload(User.profile),
            )
            .where(
                UserCourse.course_id == created_user_course_instance.course_id,
                UserCourse.user_id == created_user_course_instance.user_id,
            )
        )
        instance = db.exec(statement).first()
        return UserCourseFetch(
            user_name=instance.user.profile.name if instance.user.profile else None,
            course=instance.course,
            expected_completion_time=instance.expected_completion_time,
            started_at=instance.started_at,
            status=instance.status,
            completed_at=instance.completed_at,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already been registered to this course!"
        )


def user_course_fetch(user_id: int, db: Session) -> list[UserCourseFetch]:
    user = db.get(User, user_id)
    if not user:
        raise NoResultFound(f"User with id {user_id} not found")
    subject_statement = (
        select(Subject.title, Subject.id)
        .join(
            UserSubject,
            (UserSubject.subject_id == Subject.id) & (UserSubject.user_id == user_id),
            isouter=True,
        )
        .where(
            Subject.order is not None,
            Subject.course_id == UserCourse.course_id,
            # UserSubject.completed_at is None,
        )
        .order_by(asc(Subject.order))
        .limit(1)
        .scalar_subquery()
    )
    statement = (
        select(
            UserCourse,
            func.count(Subject.id).label("subject_counts"),
            func.count(
                expression.cast(
                    UserSubject.status == CompletionStatusEnum.COMPLETED, Integer
                )
            ).label("completed_counts"),
            subject_statement.label("next_subject"),
        )
        .select_from(UserCourse)
        .join(Course, UserCourse.course_id == Course.id)
        .join(Subject, Subject.course_id == Course.id)
        .outerjoin(UserSubject)
        .where(UserCourse.user_id == user_id)
        .group_by(UserCourse.user_id, UserCourse.course_id)
    )
    user_courses = db.exec(statement).all()
    return [
        UserCourseFetch(
            user_name=(
                user_course.user.profile.name if user_course.user.profile else None
            ),
            course=user_course.course,
            expected_completion_time=user_course.expected_completion_time,
            status=user_course.status,
            started_at=user_course.started_at,
            completed_at=user_course.completed_at,
            completion_percent=(completed_subjects / total_subjects) * 100,
            total_subjects=total_subjects,
            completed_subjects=completed_subjects,
            next_subject=next_subject,
        )
        for user_course, total_subjects, completed_subjects, next_subject in user_courses
    ]


def get_subject_detail_with_unit_counts(course_id: int, user_id: int, db: Session):
    total_unit_counts = func.count(Unit.id).label("total_units")
    completed_unit_counts = func.count(
        case((UserUnit.status == CompletionStatusEnum.COMPLETED, 1), else_=None)
    ).label("completed_units")
    unit_completed_statement = case(
        (UserUnit.status == CompletionStatusEnum.COMPLETED, True), else_=False
    ).label("is_completed")

    statement = (
        select(
            Subject.id,
            Subject.title,
            total_unit_counts,
            completed_unit_counts,
            unit_completed_statement,
        )
        .join(Unit, Unit.subject_id == Subject.id)
        .outerjoin(
            UserUnit, (UserUnit.user_id == user_id) & (UserUnit.unit_id == Unit.id)
        )
        .where(Subject.course_id == course_id)
        .group_by(Subject.id, Subject.title, UserUnit)
    )
    return db.exec(statement).all()


def user_course_fetch_by_id(
    course_id: int, user: User, db: Session
) -> UserCourseFetch | None:
    user_course = db.get(Course, course_id)
    if not user_course:
        raise NoResultFound(f"Course with id {course_id} not found")
    user_id = user.id
    subject_details = {
        subject.id: subject
        for subject in get_subject_detail_with_unit_counts(course_id, user_id, db)
    }
    subject_subquery = (
        (
            select(Subject.title).join(
                UserSubject,
                and_(
                    UserSubject.subject_id == Subject.id, UserSubject.user_id == user_id
                ),
                isouter=True,
            )
        )
        .where(
            Subject.order is not None,
            # UserSubject.completed_at is None,
            Subject.course_id == course_id,
        )
        .order_by(Subject.order)
        .limit(1)
        .scalar_subquery()
    )
    main_statement = (
        select(
            UserCourse,
            func.count(Subject.id).label("total_subjects"),
            func.count(Subject.id)
            .filter(UserSubject.status == CompletionStatusEnum.COMPLETED)
            .label("completed_counts"),
            subject_subquery.label("next_subject"),
        )
        .join(Course, Course.id == UserCourse.course_id)
        .join(Subject)
        .outerjoin(UserSubject, Subject.id == UserSubject.subject_id)
        .options(
            selectinload(UserCourse.user).selectinload(User.profile),
            selectinload(UserCourse.course)
            .selectinload(Course.subjects)
            .selectinload(Subject.units),
        )
        .where(UserCourse.user_id == user_id, UserCourse.course_id == course_id)
        .group_by(UserCourse.user_id, UserCourse.course_id)
    )
    user_course_exc = db.exec(main_statement).first()
    if not user_course_exc:
        return None
    user_course, total_subjects, completed_counts, next_subject = user_course_exc
    return UserCourseFetch(
        user_name=(user_course.user.profile.name if user_course.user.profile else None),
        course=user_course.course,
        expected_completion_time=user_course.expected_completion_time,
        status=user_course.status,
        started_at=user_course.started_at,
        completed_at=user_course.completed_at,
        completion_percent=(
            (completed_counts / total_subjects) * 100 if total_subjects else 0
        ),
        next_subject=next_subject,
        total_subjects=total_subjects,
        completed_subjects=completed_counts,
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
                        is_completed=subject_details.get(subject.id).is_completed,
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
                    if subject_details.get(subject.id)
                    else 0
                ),
            )
            for subject in user_course.course.subjects
        ],
    )


def user_course_update(user_course_id: int, user_course: BaseCommonUpdate, db: Session):
    try:
        data = user_course.model_dump()
        data["completed_at"] = datetime.now()
        course_instance = db.get(UserCourse, user_course_id)
        updated_course_instance = update_model_instance(course_instance, data)
        db.add(updated_course_instance)
        db.commit()
        db.refresh(updated_course_instance)
        return updated_course_instance
    except Exception:
        raise


def user_subject_create(user_subject: UserSubjectCreate, db: Session):
    try:
        data = user_subject.model_dump()
        user_subject_instance = create_model_instance(UserSubject, data, db)
        statement = (
            select(UserSubject)
            .options(
                joinedload(UserSubject.subject),
                selectinload(UserSubject.user).joinedload(User.profile),
            )
            .where(
                UserSubject.subject_id == user_subject_instance.subject_id,
                UserSubject.user_id == user_subject_instance.user_id,
            )
        )
        instance = db.exec(statement).first()
        return UserSubjectFetch(
            user_name=instance.user.profile.name if instance.user.profile else None,
            subject=instance.subject,
            expected_completion_time=instance.expected_completion_time,
            started_at=instance.started_at,
            status=instance.status,
            completed_at=instance.completed_at,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already started this subject!"
        )


def user_course_stats(user_id: int, db: Session) -> UserCourseStats:
    statement = (
        select(
            func.count(UserCourse.course_id).label("courses_enrolled"),
            func.count(UserCourse.course_id)
            .filter(UserCourse.status == CompletionStatusEnum.COMPLETED)
            .label("completed_courses"),
        )
        .select_from(User)
        .join(UserCourse, UserCourse.user_id == User.id)
    )
    stats = db.exec(statement).all()
    return UserCourseStats(
        completed_courses=stats[0].completed_courses,
        courses_enrolled=stats[0].courses_enrolled,
    )

def user_subject_fetch(user_id: int, db: Session) -> list[UserSubjectFetch]:
    user = db.get(User, user_id)
    if not user:
        raise NoResultFound(f"User with id {user_id} not found")
    statement = (
        select(UserSubject),
        func.count(Unit.id).label("unit_counts"),
        func.count(
            expression.cast(UserUnit.status == CompletionStatusEnum.COMPLETED, Integer)
        )
        .label("completed_counts")
        .join(Subject, Subject.id == UserUnit.subject_id)
        .join(Unit, Unit.subject_id == Subject.id)
        .outerjoin(UserUnit)
        .where(UserSubject.user_id == user_id),
    )
    user_subjects = db.exec(statement).all()
    return [
        UserSubjectFetch(
            user_name=(
                user_subject.user.profile.name if user_subject.user.profile else None
            ),
            subject=user_subject.subject,
            expected_completion_time=user_subject.expected_completion_time,
            status=user_subject.status,
            started_at=user_subject.started_at,
            completed_at=user_subject.completed_at,
            completion_percent=(completed_units / total_units) * 100,
        )
        for user_subject, total_units, completed_units in user_subjects
    ]

def user_subject_fetch_by_subject(subject_id: int, user_id: int, db: Session) -> UserSubjectUnitStatus:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NoResultFound(f"Subject with id {subject_id} not found")
    total_units = func.count(Unit.id).label("total_units")
    completed_units = func.count(Unit.id).filter(UserUnit.status == CompletionStatusEnum.COMPLETED)
    statement = (
        select(total_units, completed_units)
        .select_from(Unit)
        .join(UserUnit, and_(Unit.id == UserUnit.unit_id, UserUnit.user_id == user_id), isouter=True)
        .where(Unit.subject_id == subject_id)
        # .group_by(UserUnit.unit_id)
    )
    total_units, completed_units = db.exec(statement).first()
    return UserSubjectUnitStatus(
        total_units=total_units,
        completed_units=completed_units,
    )


def user_subject_update(
    user_subject_id: int, user_subject: BaseCommonUpdate, db: Session
):
    data = user_subject.model_dump()
    data["completed_at"] = datetime.now()
    user_subject_instance = db.get(UserSubject, user_subject_id)
    update_user_subject = update_model_instance(user_subject_instance, data)
    db.add(update_user_subject)
    db.commit()
    db.refresh(update_user_subject)
    return update_user_subject


def user_unit_create(user_unit: UserUnitCreate, db: Session):
    try:
        data = user_unit.model_dump()
        user_unit_instance = create_model_instance(UserUnit, data, db)
        return user_unit_instance

    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already started this unit!"
        )


def user_unit_fetch(user_id: int, db: Session) -> list[UserUnitFetch]:
    user = db.get(User, user_id)
    if not user:
        raise NoResultFound(f"User with id {user_id} not found")
    statement = (
        select(
            UserUnit,
            func.count(Contents.id).label("total_contents"),
            func.count(UserContent.status == CompletionStatusEnum.COMPLETED).label(
                "completed_contents"
            ),
        )
        .join(Unit, Unit.id == UserUnit.unit_id)
        .join(Contents, Contents.unit_id == Unit.id)
        .outerjoin(UserContent)
        .where(UserUnit.user_id == user_id)
    )
    user_units = db.exec(statement).all()
    return [
        UserUnitFetch(
            user_name=user_unit.user.profile.name if user_unit.user.profile else None,
            unit=user_unit.unit,
            expected_completion_time=user_unit.expected_completion_time,
            status=user_unit.status,
            started_at=user_unit.started_at,
            completed_at=user_unit.completed_at,
            completion_percent=(completed_contents / total_contents) * 100,
        )
        for user_unit, total_contents, completed_contents in user_units
    ]


def fetch_user_units_by_subject(subject_id: int, user_id: int, db: Session):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NoResultFound(f"Subject with id {subject_id} not found")
    is_started = case((and_(UserUnit.unit_id == Unit.id, UserUnit.user_id == user_id), True), else_=False)
    statement = (
        select(Unit.id, UserUnit.status, is_started)
        .join(UserUnit, and_(Unit.id == UserUnit.unit_id, UserUnit.user_id == user_id), isouter=True)
        .join(Subject)
        .where(Unit.subject_id == subject_id)
        .group_by(Unit.id, UserUnit.user_id, UserUnit.unit_id)
    )
    user_units = db.exec(statement).all()
    return [UserUnitStatus(status=unit_status if unit_status else CompletionStatusEnum.NOT_STARTED, unit_id=unit_id, is_started=is_started) for unit_id, unit_status, is_started in user_units]


def user_unit_update(user_unit_id: int, user_unit: BaseCommonUpdate, db: Session):
    try:
        data = user_unit.model_dump()
        data["completed_at"] = datetime.now()
        user_unit_instance = db.get(UserUnit, user_unit_id)
        updated_user_unit_instance = update_model_instance(user_unit_instance, data)
        db.add(updated_user_unit_instance)
        db.commit()
        db.refresh(updated_user_unit_instance)
        return updated_user_unit_instance
    except Exception:
        raise


def user_content_create(user_content: UserContentCreate, db: Session):
    try:
        data = user_content.model_dump()
        user_content_instance = create_model_instance(UserContent, data, db)
        statement = (
            select(UserContent)
            .options(
                joinedload(UserContent.content),
                selectinload(UserContent.user).joinedload(User.profile),
            )
            .where(
                UserContent.user_id == user_content_instance.user_id,
                UserContent.content_id == user_content_instance.content_id,
            )
        )
        instance = db.exec(statement).first()
        return UserContentFetch(
            user_name=instance.user.profile.name if instance.user.profile else None,
            content=instance.content,
            expected_completion_time=instance.expected_completion_time,
            started_at=instance.started_at,
            status=instance.status,
            completed_at=instance.completed_at,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already started this content!"
        )


def user_content_fetch(user_id: int, db: Session) -> list[UserContentFetch]:
    user = db.get(User, user_id)
    if not user:
        raise NoResultFound(f"User with id {user_id} not found")
    statement = (
        select(UserContent)
        .options(
            joinedload(UserContent.content),
            selectinload(UserContent.user).joinedload(User.profile),
        )
        .where(UserContent.user_id == user_id)
    )
    user_contents = db.exec(statement).all()
    return [
        UserContentFetch(
            user_name=(
                user_content.user.profile.name if user_content.user.profile else None
            ),
            content=user_content.content,
            expected_completion_time=user_content.expected_completion_time,
            status=user_content.status,
            started_at=user_content.started_at,
            completed_at=user_content.completed_at,
        )
        for user_content in user_contents
    ]


def user_content_update(
    user_content_id: int, user_content: BaseCommonUpdate, db: Session
):
    try:
        data = user_content.model_dump()
        user_content_instance = db.get(UserContent, user_content_id)
        updated_user_content_instance = update_model_instance(
            user_content_instance, data
        )
        db.add(updated_user_content_instance)
        db.commit()
        db.refresh(updated_user_content_instance)
        return updated_user_content_instance
    except Exception:
        raise
