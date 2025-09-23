from datetime import datetime

from pydantic import BaseModel, Field

from app.api.v1.schemas.users import UserFetchSchema
from app.services.enum.extras import AchievementRuleSet


class StreakTypeCreate(BaseModel):
    title: str
    description: str
    is_active: bool


class StreakTypeUpdate(BaseModel):
    title: str | None
    description: str | None
    is_active: bool | None = None


class StreakTypeFetch(StreakTypeCreate):
    id: int


class UserStreakCreate(BaseModel):
    streak_by_id: int
    streak_type_id: int
    current_streak: int
    longest_streak: int
    last_action: datetime = Field(default_factory=datetime.now)


class UserStreak(BaseModel):
    id: int
    streak_by: UserFetchSchema
    streak_type: StreakTypeFetch
    current_streak: int
    longest_streak: int
    last_action: datetime


class AchievementCreate(BaseModel):
    title: str
    icon: str
    description: str
    rule_type: AchievementRuleSet | None = None
    threshold: int | None = None
    is_expirable: bool = False
    is_active: bool
    streak_type_id: int | None = None


class AchievementUpdate(BaseModel):
    title: str | None = None
    icon: str | None = None
    description: str | None = None
    rule_type: AchievementRuleSet | None = None
    threshold: int | None = None
    is_expirable: bool | None = None
    is_active: bool | None = None
    streak_type_id: int | None = None


class AchievementFetch(AchievementCreate):
    id: int

    class Config:
        from_attributes = True


class UserAchievementsFetch(BaseModel):
    id: int
    achieved_by: UserFetchSchema
    achievement_type: AchievementFetch
    achieved_at: datetime


class AllUserAchievements(BaseModel):
    streak: int
    achievements: list[UserAchievementsFetch] = []
