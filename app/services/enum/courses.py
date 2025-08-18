from enum import Enum


class CompletionStatusEnum(Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class PaymentMethod(Enum):
    PAYPAL = "PAYPAL"
    STRIPE = "STRIPE"
    GPAY = "GPAY"
    MOBILE_BANKING = "MOBILE_BANKING"


class ContentTypeEnum(Enum):
    VIDEO = "VIDEO"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    CODE = "CODE"


class LevelEnum(Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    EXPERT = "EXPERT"