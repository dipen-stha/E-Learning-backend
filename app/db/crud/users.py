from datetime import datetime

import humanize

from fastapi import UploadFile
from sqlalchemy import extract
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, func, select

from app.api.v1.schemas.users import (
    MinimalUserFetch,
    ProfileSchema,
    StudentFetchSchema,
    UserCreateSchema,
    UserFetchSchema,
    UserStats,
    UserUpdateSchema,
)
from app.db.models.common import UserCourse
from app.db.models.enrollment import CourseEnrollment
from app.db.models.users import Profile, User
from app.services.auth.hash import get_password_hash
from app.services.enum.courses import CompletionStatusEnum
from app.services.enum.users import UserRole
from app.services.utils.crud_utils import update_model_instance, validate_unique_field
from app.services.utils.files import format_file_path, image_save


def get_user_by_id(user_id: int, db: Session) -> UserFetchSchema | None:
    user = db.exec(
        select(User).options(joinedload(User.profile)).where(User.id == user_id)
    ).first()
    return UserFetchSchema.from_orm(user)


def get_user_by_username(username: str, db: Session) -> User | None:
    user = db.exec(select(User).where(User.username == username)).first()
    return user


def update_user_login(user: User, db: Session):
    user.last_login = datetime.now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def create_user(
    user_data: UserCreateSchema, db: Session, image: UploadFile or None = None
) -> UserFetchSchema:
    if image:
        image = str(await image_save(image))
    user_instance = User(
        email=user_data.email,
        username=user_data.username,
        password=get_password_hash(user_data.password),
    )
    db.add(user_instance)
    db.flush()
    profile_instance = Profile(
        user_id=user_instance.id,
        name=user_data.name,
        gender=user_data.gender,
        dob=user_data.dob,
        avatar=image,
    )
    db.add(profile_instance)
    db.commit()
    db.refresh(profile_instance)
    return UserFetchSchema.from_orm(user_instance)


def get_user_list_by_role(
    user_role: UserRole or None, db: Session
) -> list[UserFetchSchema]:
    statement = (
        select(User).join(Profile, isouter=True).where(Profile.role == user_role)
    )
    user_instances = db.exec(statement)
    return [UserFetchSchema.from_orm(user) for user in user_instances]


async def update_user(
    user_id: int,
    user_data: UserUpdateSchema,
    db: Session,
    image: UploadFile | None = None,
):
    try:
        user_instance = db.get(User, user_id)
        if not user_instance:
            raise NoResultFound(f"User with pk {user_id} not found")
        profile_instance = db.exec(
            select(Profile).where(Profile.user_id == user_id)
        ).first()
        username = user_data.username
        email = user_data.email
        validate_unique_field(User, "username", username, db, user_instance)
        validate_unique_field(User, "email", email, db, user_instance)
        user_fields = ["username", "email", "password", "is_active"]
        profile_fields = ["name", "gender", "dob", "avatar"]
        update_data = user_data.model_dump(exclude_none=True)
        user_data_update = {
            key: value for key, value in update_data.items() if key in user_fields
        }
        password = user_data_update.pop("password")
        if password:
            user_data_update["password"] = get_password_hash(password)
        profile_data = {
            key: value for key, value in update_data.items() if key in profile_fields
        }
        if image:
            user_image = str(await image_save(image))
            if user_image:
                profile_data["avatar"] = user_image
        updated_user_instance = update_model_instance(user_instance, user_data_update)
        updated_profile_instance = update_model_instance(profile_instance, profile_data)
        db.add(updated_user_instance)
        db.commit()
        db.refresh(updated_user_instance)
        return updated_user_instance
    except Exception as e:
        db.rollback()
        raise e


def fetch_user_by_id(user_id: int, db: Session) -> UserFetchSchema | None:
    user, profile = db.exec(
        select(User, Profile)
        .join(Profile, Profile.user_id == User.id)
        .where(User.id == user_id)
    ).first()
    if not user:
        raise NoResultFound(f"User with pk {user_id} not found")
    return UserFetchSchema(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        profile=ProfileSchema(
            name=profile.name,
            dob=profile.dob,
            gender=profile.gender,
            avatar=format_file_path(profile.avatar),
            role=profile.role,
        ),
    )


def get_students_list(db: Session) -> list[StudentFetchSchema]:

    sub_query = (
        select(
            CourseEnrollment.user_id,
            func.coalesce(func.count(CourseEnrollment.course_id), 0).label(
                "total_courses"
            ),
            func.coalesce(
                func.count(UserCourse.course_id).filter(
                    UserCourse.status == CompletionStatusEnum.COMPLETED
                ),
                0,
            ).label("completed_courses"),
        )
        .group_by(CourseEnrollment.user_id, UserCourse.course_id)
        .subquery()
    )
    statement = (
        select(User, Profile, sub_query.c.total_courses, sub_query.c.completed_courses)
        .where(Profile.role == UserRole.STUDENT)
        .join(Profile, Profile.user_id == User.id)
        .outerjoin(sub_query, sub_query.c.user_id == User.id)
        .options(joinedload(User.profile), selectinload(User.user_course_links))
        .order_by(User.id)
    )
    student_list = db.exec(statement).all()
    return [
        StudentFetchSchema(
            id=user.id,
            profile=ProfileSchema(
                name=profile.name,
                gender=profile.gender,
                dob=profile.dob,
                avatar=format_file_path(profile.avatar),
                role=profile.role,
            ),
            email=user.email,
            is_active=user.is_active,
            last_login=f"{humanize.naturaldelta(datetime.now() - user.last_login) + " ago" if user.last_login else 'Not Logged In'}",
            total_courses=total_courses if total_courses else 0,
            courses_completed=completed_courses if completed_courses else 0,
            joined_date=user.created_at.date(),
        )
        for user, profile, total_courses, completed_courses in student_list
    ]


def get_minimal_user_list(db: Session) -> list[MinimalUserFetch]:
    users = db.exec(
        select(User.id, Profile.name)
        .where(User.id == Profile.user_id, Profile.role == UserRole.TUTOR)
        .join(Profile)
    ).all()
    return [MinimalUserFetch(id=user.id, name=user.name) for user in users]


def get_user_stats(role: UserRole, db: Session):
    current_month = datetime.now().month
    statement = (
        select(
            func.count(User.id).label("total_count"),
            func.count(User.id).filter(User.is_active).label("active_count"),
            func.count(User.id).filter(not User.is_active).label("suspended_count"),
            func.count(User.id)
            .filter(extract("month", User.created_at) == current_month)
            .label("monthly_creation"),
            func.count(User.id)
            .filter(extract("month", User.created_at) != current_month)
            .label("last_month_count"),
        )
        .join(Profile, Profile.user_id == User.id)
        .where(Profile.role == role)
    )
    total_count, active_count, suspended_count, monthly_creation, last_month_count = (
        db.exec(statement).first()
    )
    return UserStats(
        total_count=total_count,
        active_count=active_count,
        suspended_count=suspended_count,
        monthly_creation=monthly_creation,
        percent_total_count=(
            round(
                (total_count / (last_month_count if last_month_count else total_count))
                * 100,
                2,
            )
            if total_count != last_month_count
            else 0
        ),
        percent_active_count=round((active_count / total_count) * 100, 2),
        percent_monthly_creation=round(
            (
                monthly_creation
                / (last_month_count if last_month_count else monthly_creation)
            )
            * 100,
            2,
        ),
        percent_suspended_count=round((suspended_count / total_count) * 100, 2),
    )
