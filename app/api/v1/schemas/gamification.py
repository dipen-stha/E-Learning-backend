from datetime import datetime

from pydantic import BaseModel, Field

from app.api.v1.schemas.users import ProfileSchema, UserFetchSchema


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
    last_action:datetime = Field(default_factory=datetime.now)


class UserStreak(BaseModel):
    id: int
    streak_by: UserFetchSchema
    streak_type: StreakTypeFetch
    current_streak: int
    longest_streak: int
    last_action: datetime

