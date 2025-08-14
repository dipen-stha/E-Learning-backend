from sqlalchemy.orm import joinedload
from sqlmodel import select, Session

from app.api.v1.schemas.users import UserCreateSchema, UserFetchSchema
from app.db.models.users import Profile, User
from app.services.auth.hash import get_password_hash
from app.services.enum.users import UserRole
from app.services.utils.files import image_save

from fastapi import UploadFile


def get_user_by_id(user_id: int, db: Session) -> UserFetchSchema | None:
    user = db.exec(
        select(User).options(joinedload(User.profile)).where(User.id == user_id)
    ).first()
    return UserFetchSchema.from_orm(user)


def get_user_by_username(username: str, db: Session) -> User | None:
    user = db.exec(select(User).where(User.username == username)).first()
    return user


def create_user(
    user_data: UserCreateSchema, db: Session, image: UploadFile
) -> UserFetchSchema:
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
