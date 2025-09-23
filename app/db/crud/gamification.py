from datetime import datetime, timedelta

from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.api.v1.schemas.gamification import (
    AchievementCreate,
    AchievementFetch,
    AchievementUpdate,
    AllUserAchievements,
    StreakTypeCreate,
    StreakTypeFetch,
    StreakTypeUpdate,
    UserStreakCreate,
)
from app.db.models.gamification import (
    Achievements,
    StreakType,
    UserAchievements,
    UserStreak,
)
from app.db.models.users import User
from app.services.enum.extras import AchievementRuleSet
from app.services.utils.crud_utils import (
    map_model_with_type,
    update_model_instance,
    validate_instances_existence,
)


def fetch_all_streak_types(db: Session):
    statement = (
        select(StreakType).where(StreakType.is_active).order_by(StreakType.id.desc())
    )
    streak_types = db.exec(statement).all()
    return [
        StreakTypeFetch(
            id=streak_type.id,
            title=streak_type.title,
            description=streak_type.description,
            is_active=streak_type.is_active,
        )
        for streak_type in streak_types
    ]


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


def update_streak_type(
    streak_type_id: int, streak_type_data: StreakTypeUpdate, db: Session
):
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
        streak_type = db.exec(
            select(StreakType).where(StreakType.id == streak_type_id)
        ).first()
        if not streak_type:
            raise NoResultFound(f"Streak Type with id {streak_type_id} not found")
        return StreakTypeFetch(
            id=streak_type.id,
            title=streak_type.title,
            description=streak_type.description,
            is_active=streak_type.is_active,
        )
    except Exception as e:
        raise e


def create_or_update_user_streak(user_id: int, db: Session):
    try:
        streak_type = db.exec(
            select(StreakType).where(StreakType.title == "Unit Completion Streak")
        ).first()
        user_streak = db.exec(
            select(UserStreak).where(
                UserStreak.streak_by_id == user_id,
                UserStreak.streak_type_id == streak_type.id,
            )
        ).first()
        if user_streak:
            if user_streak.last_action.date() == datetime.now().date():
                return user_streak
            elif user_streak.last_action >= datetime.now().today() - timedelta(days=1):
                user_streak.current_streak = user_streak.current_streak + 1
            elif user_streak.last_action < datetime.now() - timedelta(days=1):
                user_streak.current_streak = 1
            else:
                return user_streak
            if user_streak.longest_streak < user_streak.current_streak:
                user_streak.longest_streak = user_streak.current_streak
                user_streak.last_action = datetime.now()
            db.add(user_streak)
        else:
            user_streak_data = UserStreakCreate(
                streak_by_id=user_id,
                streak_type_id=streak_type.id,
                current_streak=1,
                longest_streak=1,
                last_action=datetime.now(),
            )
            user_streak = UserStreak(**user_streak_data.model_dump())
            db.add(user_streak)
        db.commit()
        db.refresh(user_streak)
    except Exception as e:
        db.rollback()
        raise e


def create_achievement_type(achievement: AchievementCreate, db: Session):
    try:
        data = achievement.model_dump()
        streak_type_id = data["streak_type_id"]
        if streak_type_id:
            streak_type_instance = db.get(StreakType, streak_type_id)
            if not streak_type_instance:
                raise NoResultFound(f"Streak Type with id {streak_type_id} not found")

        achievement_instance = Achievements(**data)
        db.add(achievement_instance)
        db.commit()
        db.refresh(achievement_instance)
        return achievement_instance
    except Exception as e:
        db.rollback()
        raise e


def update_achievement_type(
    achievement_id: int, achievement: AchievementUpdate, db: Session
):
    try:
        achievement_instance = db.exec(
            select(Achievements).where(Achievements.id == achievement_id)
        ).first()
        if not achievement_instance:
            raise NoResultFound(f"Achievement with id {achievement_id} not found")
        data = achievement.model_dump()
        streak_type_id = data["streak_type_id"]
        if streak_type_id:
            streak_type_instance = db.get(StreakType, streak_type_id)
            if not streak_type_instance:
                raise NoResultFound(f"Streak Type with id {streak_type_id} not found")

        updated_achievement_instance = update_model_instance(achievement_instance, data)
        db.add(updated_achievement_instance)
        db.commit()
        db.refresh(updated_achievement_instance)
        return updated_achievement_instance
    except Exception as e:
        db.rollback()
        raise e


def fetch_all_achievements(db: Session):
    statement = select(Achievements).where(Achievements.is_active)
    achievements = db.exec(statement).all()
    return [
        AchievementFetch.model_validate(achievement) for achievement in achievements
    ]


def create_user_achievement(
    user_id: int, achievement_id: int, db: Session, streak_type_id: int | None = None
):
    try:
        if not db.get(User, user_id):
            raise NoResultFound(f"User with id {user_id} not found")
        if not db.get(Achievements, achievement_id):
            raise NoResultFound(f"Achievement with id {achievement_id} not found")

        existing_user_achievement_statement = select(UserAchievements).where(
            UserAchievements.achieved_by_id == user_id,
            UserAchievements.achievement_type_id == achievement_id,
        )
        if streak_type_id:
            if not db.get(StreakType, streak_type_id):
                raise NoResultFound(f"Streak type with id {streak_type_id} not found")
        if db.exec(existing_user_achievement_statement).first():
            return
        new_user_achievement = UserAchievements(
            achieved_by_id=user_id,
            achievement_type_id=achievement_id,
            achieved_at=datetime.now(),
        )
        db.add(new_user_achievement)
        db.commit()
        db.refresh(new_user_achievement)
        return new_user_achievement
    except Exception as e:
        db.rollback()
        raise e


def fetch_achievement_by_id(achievement_id: int, db: Session):
    statement = select(Achievements).where(Achievements.id == achievement_id)
    achievement = db.exec(statement).first()
    return AchievementFetch.model_validate(achievement)


def fetch_all_user_achievements(user_id: int, db: Session):
    try:
        user_streak = db.exec(
            select(UserStreak.current_streak).where(UserStreak.streak_by_id == user_id)
        ).first()
        return AllUserAchievements(streak=user_streak)
    except Exception as e:
        raise e


def check_and_create_user_achievements(
    rule_type: AchievementRuleSet, user_id: int, db: Session
):
    try:
        achievements = db.exec(
            select(Achievements.id, Achievements.threshold).where(
                Achievements.rule_type == rule_type
            )
        ).all()
        common_model_data, data_count = map_model_with_type(rule_type, user_id)
        eligible_achievements_ids = [
            key for key, value in achievements if value <= data_count
        ]
        existing_user_achievements = db.exec(
            select(UserAchievements.id)
            .join(Achievements, Achievements.id == UserAchievements.achievement_type_id)
            .where(
                UserAchievements.achieved_by_id == user_id,
                Achievements.rule_type == rule_type,
            )
        ).all()
        remaining_achievements = set(eligible_achievements_ids) - set(
            existing_user_achievements
        )
        new_user_achievements = [
            UserAchievements(
                achieved_by_id=user_id,
                achievement_type_id=ach_id,
                achieved_at=datetime.now(),
            )
            for ach_id in remaining_achievements
        ]
        db.add_all(new_user_achievements)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
