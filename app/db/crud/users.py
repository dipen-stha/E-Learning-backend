from datetime import datetime, timedelta

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select, Session, func

from app.api.v1.schemas.users import UserCreateSchema, UserFetchSchema, StudentFetchSchema, MinimalUserFetch
from app.db.models.common import UserCourse
from app.db.models.users import Profile, User
from app.services.auth.hash import get_password_hash
from app.services.enum.courses import CompletionStatusEnum
from app.services.enum.users import UserRole
from app.services.utils.files import image_save

from fastapi import UploadFile
import humanize


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

def create_user(
    user_data: UserCreateSchema, db: Session, image: UploadFile or None = None
) -> UserFetchSchema:
    if image:
        image = str(image_save(image))
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


def get_students_list(db: Session) -> list[StudentFetchSchema]:

    sub_query = (
        select(
            UserCourse.user_id,
            func.coalesce(func.count(UserCourse.course_id), 0).label("total_courses"),
            func.coalesce(func.count(UserCourse.course_id).filter(UserCourse.status == CompletionStatusEnum.COMPLETED), 0).label("completed_courses"),
        )
        .group_by(UserCourse.user_id)
        .subquery()
    )
    statement = (
        select(
            User,
            Profile,
            sub_query.c.total_courses,
            sub_query.c.completed_courses
        )
        .where(Profile.role == UserRole.STUDENT)
        .join(Profile, Profile.user_id == User.id)
        .outerjoin(sub_query, sub_query.c.user_id == User.id)
        .options(
            joinedload(User.profile),
            selectinload(User.user_course_links)
        )
        .order_by(User.id)
    )
    student_list = db.exec(statement).all()
    return [
        StudentFetchSchema(
            id=user.id,
            profile=profile,
            email=user.email,
            is_active=user.is_active,
            last_login=f"{humanize.naturaldelta(datetime.now() - user.last_login) + " ago" if user.last_login else 'Not Logged In'}",
            total_courses=total_courses if total_courses else 0,
            courses_completed=completed_courses if completed_courses else 0,
            joined_date=user.created_at.date()
        ) for user, profile, total_courses, completed_courses in student_list
    ]

def get_minimal_user_list(db: Session) -> list[MinimalUserFetch]:
    users = db.exec(select(User.id, Profile.name).where(User.id == Profile.user_id, Profile.role == UserRole.TUTOR).join(Profile)).all()
    return [MinimalUserFetch(id=user.id, name=user.name) for user in users]