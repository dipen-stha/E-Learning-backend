from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload, joinedload

from app.db.models.users import User
from app.db.models.common import UserCourse, UserSubject, UserUnit, UserContent
from app.api.v1.schemas.common import (
    UserCourseCreate,
    UserSubjectCreate,
    UserUnitCreate,
    UserContentCreate,
    UserCourseFetch,
    BaseCommonUpdate,
)
from app.services.utils.crud_utils import create_model_instance, update_model_instance


def user_course_create(user_course: UserCourseCreate, db: Session) -> UserCourseFetch:
    try:
        data = user_course.model_dump()
        created_user_course_instance = create_model_instance(UserCourse, data, db)
        # import ipdb;ipdb.set_trace()
        instance = db.exec(
            select(UserCourse)
            .options(joinedload(UserCourse.course), selectinload(UserCourse.user).selectinload(User.profile))
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
            completed_at=instance.completed_at
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already been registered to this course!"
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
        return user_subject_instance
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already started this subject!"
        )


def user_subject_update(
    user_subject_id: int, user_subject: BaseCommonUpdate, db: Session
):
    try:
        data = user_subject.model_dump()
        data["completed_at"] = datetime.now()
        user_subject_instance = db.get(UserSubject, user_subject_id)
        update_user_subject = update_model_instance(user_subject_id, data)
        db.add(update_user_subject)
        db.commit()
        db.refresh(update_user_subject)
        return update_user_subject
    except Exception as e:
        raise


def user_unit_create(user_unit: UserUnitCreate, db: Session):
    try:
        data = user_unit.model_dump()
        user_unit_instance = create_model_instance(UserUnit, data, db)
        return user_unit_instance
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already started this unit!"
        )


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
        return user_content_instance
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="User has already started this content!"
        )


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
