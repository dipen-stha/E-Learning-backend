from enum import Enum


class UserGender(Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class UserRole(Enum):
    ADMIN = "Admin"
    STUDENT = "Student"
    TUTOR = "Tutor"
