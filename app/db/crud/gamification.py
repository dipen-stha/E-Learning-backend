from datetime import datetime, timedelta

from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlmodel import select, Session

from app.api.v1.schemas.gamification import StreakTypeFetch, StreakTypeCreate, StreakTypeUpdate, UserStreakCreate
from app.db.models.gamification import StreakType, UserStreak
from app.services.utils.crud_utils import validate_instances_existence, update_model_instance


def fetch_all_streak_types(db: Session):
    statement = (
        select(StreakType)
        .where(StreakType.is_active == True)
        .order_by(StreakType.id.desc())
    )
    streak_types = db.exec(statement).all()
    return [StreakTypeFetch(
        id=streak_type.id,
        title=streak_type.title,
        description=streak_type.description,
        is_active=streak_type.is_active
    ) for streak_type in streak_types]

def create_streak_type(streak_type_data: StreakTypeCreate, db: Session):
    try:
        data = streak_type_data.model_dump()
        streak_type_instance = StreakType(**data)
        db.add(streak_type_instance)
        db.commit()
        db.refresh(streak_type_instance)
        return streak_type_instance
    except Exception as e:
        db.rollback()
        raise e

def update_streak_type(streak_type_id: int, streak_type_data: StreakTypeUpdate, db: Session):
    try:
        streak_type_instance = validate_instances_existence(streak_type_id, StreakType)
        if not streak_type_instance:
            raise NoResultFound(f"Streak type with pk {streak_type_id} not found")
        data = streak_type_data.model_dump()
        update_instance = update_model_instance(streak_type_instance, data)
        db.add(update_instance)
        db.commit()
        db.refresh(update_instance)
        return update_instance
    except Exception as e:
        db.rollback()
        raise e

def remove_streak_type(streak_type_id: int, db: Session):
    try:
        streak_type_instance = validate_instances_existence(streak_type_id, StreakType)
        if not streak_type_instance:
            raise NoResultFound(f"Streak type with pk {streak_type_id} not found")
        db.delete(streak_type_instance)
        db.commit()
        return
    except Exception as e:
        db.rollback()
        raise e

def fetch_streak_type_by_id(streak_type_id: int, db: Session):
    try:
        streak_type = db.exec(select(StreakType).where(StreakType.id == streak_type_id)).first()
        if not streak_type:
            raise NoResultFound(f"Streak Type with id {streak_type_id} not found")
        return StreakTypeFetch(
            id=streak_type.id,
            title=streak_type.title,
            description=streak_type.description,
            is_active=streak_type.is_active
        )
    except Exception as e:
        raise e

def create_or_update_user_streak(user_id: int, streak_type_id: int, db: Session):
    try:
        streak_type = validate_instances_existence(streak_type_id, StreakType)
        if not streak_type:
            raise NoResultFound(f"Streak type with pk {streak_type_id} not found")

        user_streak = db.exec(select(UserStreak).where(UserStreak.streak_by_id == user_id, UserStreak.streak_type_id == streak_type_id)).first()
        if user_streak:
            if user_streak.last_action.date == datetime.now().today():
                return user_streak
            elif user_streak.last_action == datetime.now().today() - timedelta(days=1):
                user_streak.current_streak = user_streak.current_streak + 1
            elif user_streak.last_action > datetime.now().today() - timedelta(days=1):
                user_streak.current_streak  = 1
            if user_streak.longest_streak < user_streak.current_streak:
                user_streak.longest_streak = user_streak.current_streak
            user_streak.last_action = datetime.now()
            db.add(user_streak)
        else:
            user_streak_data = UserStreakCreate(
                streak_by_id=user_id,
                streak_type_id=streak_type_id,
                current_streak=1,
                longest_streak=1,
                last_action=datetime.now()
            )
            user_streak = UserStreak(**user_streak_data.model_dump())
            db.add(user_streak)
        db.commit()
        db.refresh(user_streak)
    except Exception as e:
        db.rollback()
        raise e