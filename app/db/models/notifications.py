from sqlmodel import Field, SQLModel

from app.services.enum.extras import (
    NotificationFor,
    NotificationStatus,
    NotificationType,
)
from app.services.mixins.db_mixins import BaseTimeStampMixin


class Notifications(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    notification_type: NotificationType
    created_for: NotificationFor
    status: NotificationStatus = Field(default=NotificationStatus.PENDING)
    user_id: int | None = Field(foreign_key="users.id", nullable=True)
    message: str

    __tablename__ = "notifications"
