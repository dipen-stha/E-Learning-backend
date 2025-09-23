from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db.models.assessments import Assessment
from app.db.models.common import UserCourse, UserSubject, UserUnit
from app.db.models.enrollment import CourseEnrollment
from app.db.models.gamification import UserStreak
from app.db.session.session import get_db
from app.services.enum.courses import CompletionStatusEnum, PaymentStatus
from app.services.enum.extras import AchievementRuleSet


db = next(get_db())

rule_and_model_map = {
    AchievementRuleSet.COURSE: UserCourse,
    AchievementRuleSet.SUBJECT: UserSubject,
    AchievementRuleSet.UNIT: UserUnit,
    AchievementRuleSet.STREAK: UserStreak,
    AchievementRuleSet.ENROLLMENT: CourseEnrollment,
}

user_and_model_map = {
    UserCourse: (UserCourse.user_id, UserCourse.course_id),
    UserSubject: (UserSubject.user_id, UserSubject.subject_id),
    UserUnit: (UserUnit.user_id, UserUnit.unit_id),
    UserStreak: (UserStreak.streak_by_id, UserStreak.longest_streak),
    CourseEnrollment: (CourseEnrollment.user_id, CourseEnrollment.course_id),
}

filter_and_model_map = {
    UserCourse: (UserCourse.status, CompletionStatusEnum.COMPLETED),
    UserSubject: (UserSubject.status, CompletionStatusEnum.COMPLETED),
    UserUnit: (UserUnit.status, CompletionStatusEnum.COMPLETED),
    CourseEnrollment: (CourseEnrollment.status, PaymentStatus.PAID),
}


def update_model_instance(instance: any, data: dict):
    if "id" in data.keys():
        data.pop("id")
    for key, value in data.items():
        setattr(instance, key, value)
    return instance


def get_model_instance_by_id(model: any, instance_id: int):
    db = next(get_db())
    return db.get(model, instance_id)


def create_model_instance(model: any, data: dict):
    try:
        model_instance = model(**data)
        db.add(model_instance)
        db.commit()
        db.refresh(model_instance)
        return model_instance
    except IntegrityError:
        db.rollback()
        raise IntegrityError


def validate_unique_field(
    model: any, field: str, data: any, db: Session, instance: any
):
    try:
        statement = select(model).where(getattr(model, field) == data)
        model_instance = db.exec(statement).first()
        if model_instance and (instance.id is None or model_instance.id != instance.id):
            raise IntegrityError(f"{model} with this {field} already exists")
    except Exception as e:
        raise e


def validate_instances_existence(model_id: int, model: any):
    return db.get(model, model_id)


def fetch_existing_order_assessments(subject_id: int, order: int):
    return db.exec(
        select(Assessment).where(
            Assessment.subject_id == subject_id, Assessment.order == order
        )
    ).all()


def map_model_with_type(rule_type: AchievementRuleSet, user_id: int):
    model = rule_and_model_map[rule_type]
    model_field, count_field = user_and_model_map[model]
    model_filter_field, filter_value = filter_and_model_map[model]
    statement = select(model).where(
        model_field == user_id, model_filter_field == filter_value
    )
    count_statement = select(
        func.count(count_field).filter(
            model_field == user_id, model_filter_field == filter_value
        )
    )
    return db.exec(statement).all(), db.exec(count_statement).first()
