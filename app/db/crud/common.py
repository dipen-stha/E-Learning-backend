from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import select, Session, func, asc, and_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.types import Integer
from sqlmodel.sql import expression

from app.db.models.courses import Subject, Course, Unit, Contents
from app.db.models.users import User
from app.db.models.common import UserCourse, UserSubject, UserUnit, UserContent
from app.api.v1.schemas.common import (
    UserCourseCreate,
    UserSubjectCreate,
    UserUnitCreate,
    UserContentCreate,
    UserCourseFetch,
    BaseCommonUpdate,
    UserSubjectFetch,
    UserUnitFetch,
    UserContentFetch, UserCourseStats,
)
from app.services.enum.courses import CompletionStatusEnum
from app.services.utils.crud_utils import create_model_instance, update_model_instance
from app.services.utils.files import format_file_path


def user_course_create(user_course: UserCourseCreate, db: Session) -> UserCourseFetch:
    try:
        data = user_course.model_dump()
        created_user_course_instance = create_model_instance(UserCourse, data, db)
        instance = db.exec(
            select(UserCourse)
            .options(
                joinedload(UserCourse.course),
                selectinload(UserCourse.user).selectinload(User.profile),
            )
            .where(
                UserCourse.course_id == created_user_course_instance.course_id,
                UserCourse.user_id == created_user_course_instance.user_id,
            )
        ).first()
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
        select(Subject.title).join(
            UserSubject,
            (UserSubject.subject_id == Subject.id) & (UserSubject.user_id == user_id), isouter=True
        ).where(
            Subject.order != None,
            Subject.course_id == UserCourse.course_id,
            UserSubject.completed_at == None,
        ).order_by(asc(Subject.order))
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
            subject_statement.label("next_subject")
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
            next_subject=next_subject
        )
        for user_course, total_subjects, completed_subjects, next_subject in user_courses
    ]

def user_course_fetch_by_id(course_id:int, user: User, db: Session) -> UserCourseFetch | None:
    user_course = db.get(User, course_id)
    if not user_course:
        raise NoResultFound(f"User with id {course_id} not found")
    user_id = user.id
    subject_subquery = ((
        select(Subject.title)
        .join(UserSubject, and_(UserSubject.subject_id == Subject.id, UserSubject.user_id == user_id), isouter=True)
        ).where(
            Subject.order != None,
            UserSubject.completed_at == None,
            Subject.course_id == course_id
        )
        .order_by(Subject.order)
        .limit(1)
        .scalar_subquery()
        )
    main_statement = (
        select(
            UserCourse,
            func.count(Subject.id).label("total_subjects"),
            func.count(Subject.id).filter(UserSubject.status == CompletionStatusEnum.COMPLETED).label("completed_counts"),
            subject_subquery.label("next_subject")
        )
        .join(Course, Course.id == UserCourse.course_id)
        .join(Subject)
        .outerjoin(UserSubject, Subject.id == UserSubject.subject_id)
        .options(selectinload(UserCourse.user).selectinload(User.profile))
        .where(UserCourse.user_id == user_id)
        .group_by(UserCourse.user_id, UserCourse.course_id)
    )
    user_course_exc = db.exec(main_statement).first()
    if not user_course_exc:
        return None
    user_course, total_subjects, completed_counts, next_subject = user_course_exc
    return UserCourseFetch(
            user_name=(
                user_course.user.profile.name if user_course.user.profile else None
            ),
            course=user_course.course,
            expected_completion_time=user_course.expected_completion_time,
            status=user_course.status,
            started_at=user_course.started_at,
            completed_at=user_course.completed_at,
            completion_percent=(completed_counts / total_subjects) * 100 if total_subjects else 0,
            next_subject=next_subject,
            total_subjects=total_subjects,
            completed_subjects=completed_counts,
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
    except Exception as e:
        raise


def user_subject_create(user_subject: UserSubjectCreate, db: Session):
    try:
        data = user_subject.model_dump()
        user_subject_instance = create_model_instance(UserSubject, data, db)
        instance = db.exec(
            select(UserSubject)
            .options(
                joinedload(UserSubject.subject),
                selectinload(UserSubject.user).joinedload(User.profile),
            )
            .where(
                UserSubject.subject_id == user_subject_instance.subject_id,
                UserSubject.user_id == user_subject_instance.user_id,
            )
        ).first()
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


def user_course_stats(user_id: int, db: Session)-> UserCourseStats:
    statement = (
        select(
            func.count(UserCourse.course_id).label("courses_enrolled"),
            func.count(UserCourse.course_id).filter(UserCourse.status == CompletionStatusEnum.COMPLETED).label("completed_courses"),
        ).select_from(User)
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
        func.count(expression.cast(
            UserUnit.status == CompletionStatusEnum.COMPLETED, Integer
        )).label("completed_counts")
        .join(Subject, Subject.id == UserUnit.subject_id)
        .join(Unit, Unit.subject_id == Subject.id)
        .outerjoin(UserUnit)
        .where(UserSubject.user_id == user_id)
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
            completion_percent=(completed_units/total_units) * 100
        )
        for user_subject, total_units, completed_units in user_subjects
    ]


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
        instance = db.exec(
            select(UserUnit)
            .options(
                joinedload(UserUnit.unit),
                selectinload(UserUnit.user).joinedload(User.profile),
            )
            .where(
                UserUnit.user_id == user_unit_instance.user_id,
                UserUnit.unit_id == user_unit_instance.unit_id,
            )
        ).first()
        return UserUnitFetch(
            user_name=instance.user.profile.name if instance.user.profile else None,
            unit=instance.unit,
            expected_completion_time=instance.expected_completion_time,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            status=instance.status,
        )
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
            func.count(UserContent.status == CompletionStatusEnum.COMPLETED).label("completed_contents")
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
            completion_percent=(completed_contents/total_contents) * 100
        )
        for user_unit, total_contents, completed_contents in user_units
    ]


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
    except Exception as e:
        raise


def user_content_create(user_content: UserContentCreate, db: Session):
    try:
        data = user_content.model_dump()
        user_content_instance = create_model_instance(UserContent, data, db)
        instance = db.exec(
            select(UserContent)
            .options(
                joinedload(UserContent.content),
                selectinload(UserContent.user).joinedload(User.profile),
            )
            .where(
                UserContent.user_id == user_content_instance.user_id,
                UserContent.content_id == user_content_instance.content_id,
            )
        ).first()
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
    except Exception as e:
        raise
