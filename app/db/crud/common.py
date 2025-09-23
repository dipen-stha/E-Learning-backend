from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import (
    contains_eager,
    joinedload,
    selectinload,
    with_loader_criteria,
)
from sqlalchemy.types import Integer
from sqlmodel import Session, and_, asc, case, func, select
from sqlmodel.sql import expression

from app.api.v1.schemas.common import (
    BaseCommonFetch,
    BaseCommonUpdate,
    UpcomingCourseSubjects,
    UserContentCreate,
    UserContentFetch,
    UserContentStatus,
    UserContentStatusUpdate,
    UserCourseCreate,
    UserCourseFetch,
    UserCourseStats,
    UserSubjectCreate,
    UserSubjectFetch,
    UserSubjectStatus,
    UserSubjectUnitStatus,
    UserUnitCreate,
    UserUnitFetch,
    UserUnitStatus,
    UserUnitStatusUpdate,
)
from app.api.v1.schemas.courses import BaseSubjectFetch, SubjectFetch, UserUnitDetail
from app.db.models.common import UserContent, UserCourse, UserSubject, UserUnit
from app.db.models.courses import Contents, Course, Subject, Unit
from app.db.models.enrollment import CourseEnrollment
from app.db.models.users import User
from app.services.enum.courses import CompletionStatusEnum, StatusEnum
from app.services.utils.crud_utils import create_model_instance, update_model_instance


def user_course_create(user_course: UserCourseCreate, db: Session) -> UserCourseFetch:
    try:
        data = user_course.model_dump()
        # created_user_course_instance = create_model_instance(UserCourse, data)
        user_unit_instance = UserUnit(**data)
        db.add(user_unit_instance)
        db.commit()
        db.refresh(user_unit_instance)
        return user_unit_instance
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="User has already been registered to this course!"
        )


def user_course_fetch(user_id: int, db: Session) -> list[UserCourseFetch]:
    user = db.get(User, user_id)
    if not user:
        raise NoResultFound(f"User with id {user_id} not found")
    subject_statement = (
        select(Subject.title)
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
            completion_percent=round((completed_subjects / total_subjects) * 100, 2),
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
    statement = (
        select(
            Subject.id,
            Subject.title,
            total_unit_counts,
            completed_unit_counts,
        )
        .join(Unit, Unit.subject_id == Subject.id, isouter=True)
        .join(
            UserUnit,
            (UserUnit.user_id == user_id) & (UserUnit.unit_id == Unit.id),
            isouter=True,
        )
        .where(Subject.course_id == course_id)
        .group_by(Subject.id, Subject.title)
    )
    return db.exec(statement).all()


def get_unit_details(subject_id: int, user_id: int, db: Session):
    unit_completed_statement = case(
        (UserUnit.status == CompletionStatusEnum.COMPLETED, True), else_=False
    ).label("is_completed")
    statement = (
        select(Unit.id, unit_completed_statement)
        .outerjoin(
            UserUnit, and_(UserUnit.unit_id == Unit.id, UserUnit.user_id == user_id)
        )
        .where(Unit.subject_id == subject_id)
        .group_by(Unit.id, UserUnit.status)
    )
    return db.exec(statement).all()


def fetch_subject_status_by_course_id(course_id: int, user_id: int, db: Session):
    course = db.get(Course, course_id)
    if not course:
        raise NoResultFound(f"Course with pk {course_id} not found")
    statement = (
        select(Subject.id, UserSubject.status)
        .join(
            UserSubject,
            and_(UserSubject.subject_id == Subject.id, UserSubject.user_id == user_id),
            isouter=True,
        )
        .where(Subject.course_id == course_id, Subject.status == StatusEnum.PUBLISHED)
    )
    subject_statuses = db.exec(statement).all()
    return [
        UserSubjectStatus(id=subject_id, status=user_subject_status)
        for subject_id, user_subject_status in subject_statuses
    ]


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

    units_details = {
        unit.id: unit
        for subject in subject_details.keys()
        for unit in get_unit_details(subject, user_id, db)
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
            Subject.status == StatusEnum.PUBLISHED,
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
        .join(Subject, Subject.course_id == Course.id)
        .outerjoin(UserSubject, Subject.id == UserSubject.subject_id)
        .options(
            selectinload(UserCourse.user).selectinload(User.profile),
            selectinload(UserCourse.course)
            .selectinload(Course.subjects)
            .selectinload(Subject.units),
            with_loader_criteria(Subject, Subject.status == StatusEnum.PUBLISHED),
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
            round((completed_counts / total_subjects) * 100, 2) if total_subjects else 0
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
                        is_completed=units_details.get(unit.id).is_completed,
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
                        and subject_details.get(subject.id).total_units
                        and subject_details.get(subject.id).completed_units
                    )
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
        user_subject_instance = create_model_instance(UserSubject, data)
        return BaseCommonFetch(
            expected_completion_time=user_subject_instance.expected_completion_time,
            started_at=user_subject_instance.started_at,
            status=user_subject_instance.status,
            completed_at=user_subject_instance.completed_at,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already started this subject!"
        )


def fetch_user_upcoming_subjects(db: Session, user_id: int | None = None):
    user_enrolled_courses = db.exec(
        select(CourseEnrollment).where(CourseEnrollment.user_id == user_id)
    ).all()

    next_subjects_by_course = {}

    for enrollment in user_enrolled_courses:
        course_id = enrollment.course_id
        last_completed_subject = db.exec(
            select(Subject)
            .join(UserSubject, UserSubject.subject_id == Subject.id, isouter=True)
            .where(
                UserSubject.user_id == user_id,
                Subject.course_id == course_id,
                UserSubject.status == CompletionStatusEnum.COMPLETED,
                Subject.status == StatusEnum.PUBLISHED,
            )
            .order_by(Subject.order.desc())
            .limit(1)
        ).first()
        if last_completed_subject:
            next_subject = db.exec(
                select(Subject)
                .where(
                    Subject.order > last_completed_subject.order,
                    Subject.course_id == course_id,
                    Subject.status == StatusEnum.PUBLISHED,
                )
                .order_by(asc(Subject.order))
                .limit(1)
            ).first()
        else:
            next_subject = db.exec(
                select(Subject)
                .where(
                    Subject.course_id == course_id,
                    Subject.status == StatusEnum.PUBLISHED,
                )
                .order_by(asc(Subject.order))
                .limit(1)
            ).first()
        next_subjects_by_course[course_id] = next_subject
    return [
        UpcomingCourseSubjects(
            course_id=course_id,
            subject=BaseSubjectFetch(id=value.id, title=value.title),
        )
        for course_id, value in next_subjects_by_course.items()
        if value
    ]


def user_course_stats(user_id: int, db: Session) -> UserCourseStats:
    statement = (
        select(
            func.count(CourseEnrollment.course_id.distinct()).label("courses_enrolled"),
            func.count(UserCourse.course_id.distinct())
            .filter(UserCourse.status == CompletionStatusEnum.COMPLETED)
            .label("completed_courses"),
            func.coalesce(
                func.sum(Course.completion_time.distinct()).filter(
                    UserCourse.status == CompletionStatusEnum.COMPLETED,
                    UserCourse.course_id == Course.id,
                ),
                0,
            ).label("hours_learned"),
            func.coalesce(
                func.sum(Subject.completion_time.distinct()).filter(
                    UserSubject.status == CompletionStatusEnum.COMPLETED,
                    UserSubject.subject_id == Subject.id,
                ),
                0,
            ).label("subjects_completed"),
        )
        .select_from(User)
        .join(CourseEnrollment, CourseEnrollment.user_id == user_id, isouter=True)
        .join(UserCourse, UserCourse.user_id == user_id, isouter=True)
        .join(Course, Course.id == UserCourse.course_id)
        .join(Subject, Subject.course_id == Course.id, isouter=True)
        .join(UserSubject, UserSubject.subject_id == Subject.id, isouter=True)
        .where(User.id == user_id)
    )
    stats = db.exec(statement).first()
    return UserCourseStats(
        completed_courses=stats.completed_courses,
        courses_enrolled=stats.courses_enrolled,
        hours_learned=stats.hours_learned,
        subject_completed=stats.subjects_completed,
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


def user_subject_fetch_by_subject(
    subject_id: int, user_id: int, db: Session
) -> UserSubjectUnitStatus:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NoResultFound(f"Subject with id {subject_id} not found")
    total_units = func.count(Unit.id).label("total_units")
    completed_units = func.count(Unit.id).filter(
        UserUnit.status == CompletionStatusEnum.COMPLETED
    )
    statement = (
        select(total_units, completed_units)
        .select_from(Unit)
        .join(
            UserUnit,
            and_(Unit.id == UserUnit.unit_id, UserUnit.user_id == user_id),
            isouter=True,
        )
        .where(Unit.subject_id == subject_id)
        # .group_by(UserUnit.unit_id)
    )
    total_units, completed_units = db.exec(statement).first()
    return UserSubjectUnitStatus(
        total_units=total_units,
        completed_units=completed_units,
        completion_percent=(
            round(completed_units / total_units * 100, 2)
            if (completed_units and total_units)
            else 0
        ),
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
        user_unit_instance = create_model_instance(UserUnit, data)
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
    statement = (
        select(Unit)
        .join(Subject)
        .outerjoin(
            UserUnit, and_(Unit.id == UserUnit.unit_id, UserUnit.user_id == user_id)
        )
        .options(
            contains_eager(Unit.user_unit_links),
            selectinload(Unit.contents).selectinload(Contents.user_content_links),
        )
        .where(Unit.subject_id == subject_id)
    )
    user_units = db.exec(statement).unique().all()
    return [
        UserUnitStatus(
            unit_id=unit.id,
            status=(
                unit.user_unit_links[0].status
                if unit.user_unit_links
                else CompletionStatusEnum.NOT_STARTED
            ),
            contents=[
                UserContentStatus(
                    content_id=content.id,
                    status=(
                        content.user_content_links[0].status
                        if content.user_content_links
                        else CompletionStatusEnum.NOT_STARTED
                    ),
                )
                for content in unit.contents
            ],
        )
        for unit in user_units
    ]


def user_unit_status_update(user_unit: UserUnitStatusUpdate, db: Session):
    unit = db.get(Unit, user_unit.unit_id)
    if not unit:
        raise NoResultFound(f"Unit with id {user_unit.unit_id} not found")
    user_unit_instance = db.exec(
        select(UserUnit).where(
            UserUnit.user_id == user_unit.user_id, UserUnit.unit_id == user_unit.unit_id
        )
    ).first()
    if not user_unit_instance:
        raise NoResultFound("Not records of user for this unit found")
    if user_unit_instance == CompletionStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=400, detail="User has already completed this unit!"
        )
    data = user_unit.model_dump(exclude_none=True)
    updated_user_unit = update_model_instance(user_unit_instance, data)
    db.add(updated_user_unit)
    db.commit()
    db.refresh(updated_user_unit)
    return updated_user_unit


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
        content_id = user_content.content_id
        content_instance = db.get(Contents, content_id)
        if not content_instance:
            raise NoResultFound(f"Content with id {content_id} not found")
        user_unit_instance = db.exec(
            select(UserUnit).where(
                UserUnit.user_id == user_content.user_id,
                UserUnit.unit_id == content_instance.unit_id,
            )
        ).first()
        data = user_content.model_dump()
        if not user_unit_instance:
            content_id = data.pop("content_id")
            data["unit_id"] = content_instance.unit_id
            user_unit = UserUnitCreate(**data)
            user_unit_create(user_unit, db)
            data["content_id"] = content_id
        user_content_instance = create_model_instance(UserContent, data)
        return user_content_instance
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already started this content!"
        )


def user_content_status_update(user_content_data: UserContentStatusUpdate, db: Session):
    try:
        content = db.get(Contents, user_content_data.content_id)
        if not content:
            raise NoResultFound(
                f"Content with id {user_content_data.content_id} not found"
            )
        user_content_instance = db.exec(
            select(UserContent).where(
                UserContent.user_id == user_content_data.user_id,
                UserContent.content_id == user_content_data.content_id,
            )
        ).first()
        unit_instance = db.exec(select(Unit).where(Unit.id == content.unit_id)).first()
        if not user_content_instance:
            raise NoResultFound("User has not started this content")
        if user_content_instance.status == CompletionStatusEnum.COMPLETED:
            raise HTTPException(
                status_code=400, detail="User has already completed this content!"
            )
        data = user_content_data.model_dump()
        updated_user_content_instance = update_model_instance(
            user_content_instance, data
        )
        updated_user_content_instance.completed_at = datetime.now()
        db.add(updated_user_content_instance)
        user_unit_instance = db.exec(
            select(UserUnit).where(
                UserUnit.user_id == user_content_data.user_id,
                UserUnit.unit_id == content.unit_id,
            )
        ).first()
        unit_contents = db.exec(
            select(UserContent.status).where(
                UserContent.user_id == user_content_data.user_id,
                UserContent.content_id == user_content_data.content_id,
            )
        ).all()
        course_completed = False
        is_all_contents_completed = all(
            item == CompletionStatusEnum.COMPLETED for item in unit_contents
        )
        if is_all_contents_completed:
            user_unit_instance.status = CompletionStatusEnum.COMPLETED
            user_unit_instance.completed_at = datetime.now()
            db.add(user_unit_instance)
            db.flush()
            user_units = db.exec(
                select(UserUnit.status).where(
                    UserUnit.unit_id == unit_instance.id,
                    UserUnit.user_id == user_content_data.user_id,
                )
            ).all()
            is_all_units_completed = all(
                user_unit == CompletionStatusEnum.COMPLETED for user_unit in user_units
            )
            if is_all_units_completed:
                subject_instance = db.exec(
                    select(Subject).where(
                        Subject.id == unit_instance.subject_id,
                        Subject.status == StatusEnum.PUBLISHED,
                    )
                ).first()
                user_subject_instance = db.exec(
                    select(UserSubject).where(
                        UserSubject.subject_id == subject_instance.id,
                        UserSubject.user_id == user_content_data.user_id,
                    )
                ).first()
                user_subject_instance.status = CompletionStatusEnum.COMPLETED
                user_subject_instance.completed_at = datetime.now()
                db.add(user_subject_instance)
                db.flush()
                user_subjects = db.exec(
                    select(UserSubject.status).where(
                        UserSubject.subject_id == subject_instance.id
                    )
                ).all()
                is_all_subjects_completed = all(
                    user_subject == CompletionStatusEnum.COMPLETED
                    for user_subject in user_subjects
                )
                if is_all_subjects_completed:
                    user_course = db.exec(
                        select(UserCourse).where(
                            UserCourse.course_id == subject_instance.course_id
                        )
                    ).first()
                    user_course.status = CompletionStatusEnum.COMPLETED
                    user_course.completed_at = datetime.now()
                    course_completed = True
                    db.add(user_course)
                    db.flush()
        db.commit()
        db.refresh(updated_user_content_instance)
        return True, course_completed
    except Exception as e:
        db.rollback()
        raise e


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
