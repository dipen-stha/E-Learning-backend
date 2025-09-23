from enum import Enum


class NotificationType(Enum):
    ACHIEVEMENT = "ACHIEVEMENT"
    ENROLLED = "ENROLLED"
    COMPLETED = "COMPLETED"
    WARNING = "WARNING"


class NotificationFor(Enum):
    ALL = "ALL"
    STUDENT = "STUDENT"
    TUTOR = "TUTOR"


class NotificationStatus(Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class AchievementRuleSet(Enum):
    COURSE = "COURSE"
    SUBJECT = "SUBJECT"
    UNIT = "UNIT"
    STREAK = "STREAK"
    ENROLLMENT = "ENROLLMENT"
