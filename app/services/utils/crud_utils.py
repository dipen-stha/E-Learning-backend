from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db.session.session import get_db


def update_model_instance(instance: any, data: dict):
    for key, value in data.items():
        setattr(instance, key, value)
    return instance


def get_model_instance_by_id(model: any, instance_id: int):
    db = next(get_db())
    return db.get(model, instance_id)


def create_model_instance(model: any, data: dict, db: Session):
    try:
        model_instance = model(**data)
        db.add(model_instance)
        db.commit()
        db.flush(model_instance)
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
