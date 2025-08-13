from datetime import datetime, date

from sqlmodel import SQLModel, Field, Relationship

from app.services.mixins.db_mixins import BaseTimeStampMixin

class Achievements(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255)
    icon: str = Field(max_length=50)
    description: str | None
    is_expirable: bool = Field(default=False)
    is_active: bool = Field(default=True)

    achievements_users: list["UserAchievements"] = Relationship(back_populates="achievement_type")

    __tablename__ = "achievements"


class StreakType(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255)
    description: str | None
    is_active: bool = Field(default=True)

    streaks_users: list["UserStreak"] = Relationship(back_populates="streak_type")

    __tablename__ = "streak_types"


class UserStreak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    streak_by_id : int = Field(foreign_key="users.id", index=True)
    streak_type_id : int = Field(foreign_key="streak_types.id", index=True)
    current_streak: int = Field(default=0, ge=0)
    longest_streak: int = Field(default=0, ge=0)
    last_action: datetime | None = Field(nullable=True)

    streak_type: StreakType = Relationship(back_populates="streaks_users")
    streak_by: "User" = Relationship(back_populates="users_streaks")

    __tablename__ = "user_streaks"


class UserAchievements(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    achieved_by_id: int = Field(foreign_key="users.id", index=True)
    achievement_type_id: int = Field(foreign_key="achievements.id", index=True)
    achieved_at: datetime | None = Field(nullable=True)

    achieved_by: "User" = Relationship(back_populates="achieved")
    achievement_type: Achievements = Relationship(back_populates="achievements_users")

    __tablename__ = "user_achievements"



