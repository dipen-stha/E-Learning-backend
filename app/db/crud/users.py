from sqlmodel import select, Session

from app.api.v1.schemas.users import UserFetchSchema, UserCreateSchema
from app.db.models.users import User, Profile
from app.services.auth.hash import get_password_hash


def get_user_by_id(user_id: int, db: Session) -> User | None:
    user = db.get(User, user_id)
    return user

def get_user_by_username(username: str, db: Session) -> User | None:
    user = db.exec(select(User).where(User.username == username)).first()
    return user

def create_user(user_data: UserCreateSchema, db: Session) -> UserFetchSchema:
    user_instance = User(
        email=user_data.email,
        username=user_data.username,
        password=get_password_hash(user_data.password)
    )
    db.add(user_instance)
    db.flush()
    profile_instance = Profile(
        user_id=user_instance.id,
        name=user_data.name,
        gender=user_data.gender,
        dob=user_data.dob,
    )
    db.add(profile_instance)
    db.commit()
    db.refresh(profile_instance)
    return UserFetchSchema.from_orm(user_instance)